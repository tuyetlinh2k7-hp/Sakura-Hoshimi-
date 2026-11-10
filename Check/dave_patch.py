"""
Monkey-patch module to fix DAVE E2EE protocol support in discord.py 2.7.1 (PR #10548).
Fixes issue where davey 0.2.0 requires prepare_transition and execute_transition calls,
enabling can_encrypt to become True so that Discord voice packets are encrypted and heard.
"""
import struct
import logging
from typing import Set, Dict, Any, Optional

import discord
import discord.voice_client as d_vc
import discord.voice_state as d_vs
import discord.gateway as d_gw

_log = logging.getLogger(__name__)

try:
    import davey
    has_dave = True
except ImportError:
    has_dave = False


_PATCH_APPLIED = False


def apply_dave_patch():
    global _PATCH_APPLIED
    if _PATCH_APPLIED or not has_dave:
        return
    _PATCH_APPLIED = True

    print("[DAVE Patch] ✅ Đã kích hoạt bản vá DAVE E2EE 0.2.0 cho discord.py 2.7.1 (PR #10548).")

    # 1. Patch VoiceConnectionState
    orig_init = d_vs.VoiceConnectionState.__init__

    def patched_init(self, voice_client, *, hook=None):
        orig_init(self, voice_client, hook=hook)
        self.connected_user_ids: Set[int] = set()

    d_vs.VoiceConnectionState.__init__ = patched_init

    @property
    def patched_can_encrypt(self) -> bool:
        return (
            self.dave_protocol_version != 0
            and not getattr(self, "dave_downgraded", False)
            and self.dave_session is not None
            and self.dave_session.ready
        )

    d_vs.VoiceConnectionState.can_encrypt = patched_can_encrypt

    async def patched_reinit_dave_session(self) -> None:
        self.dave_pending_transitions.clear()
        if self.dave_protocol_version > 0:
            session = self.dave_session
            if session is not None:
                session.reinit(self.dave_protocol_version, self.user.id, self.voice_client.channel.id)
            else:
                session = davey.DaveSession(self.dave_protocol_version, self.user.id, self.voice_client.channel.id)
                self.dave_session = session

            if getattr(self, "dave_downgraded", False):
                session.set_passthrough_mode(True)

            await self.voice_client.ws.send_binary(
                d_gw.DiscordVoiceWebSocket.MLS_KEY_PACKAGE, session.get_serialized_key_package()
            )
        elif self.dave_session:
            self.dave_session.reset()
            self.dave_session.set_passthrough_mode(True)

    d_vs.VoiceConnectionState.reinit_dave_session = patched_reinit_dave_session

    async def patched_execute_transition(self, transition_id: int) -> None:
        _log.debug('Executing transition id %d', transition_id)
        if transition_id not in self.dave_pending_transitions:
            _log.warning("Received execute transition, but we don't have a pending transition for id %d", transition_id)
            return

        if self.dave_session and transition_id != 0:
            try:
                if not self.dave_session.execute_transition(transition_id):
                    self.dave_pending_transitions.pop(transition_id, None)
                    _log.warning('Failed to execute DAVE transition id %d: davey did not execute it', transition_id)
                    return
            except Exception:
                self.dave_pending_transitions.pop(transition_id, None)
                _log.exception('Failed to execute DAVE transition id %d', transition_id)
                return

        old_version = self.dave_protocol_version
        self.dave_protocol_version = self.dave_pending_transitions.pop(transition_id)

        if old_version != self.dave_protocol_version and self.dave_protocol_version == 0:
            self.dave_downgraded = True
            _log.debug('DAVE Session downgraded')
        elif transition_id > 0 and getattr(self, "dave_downgraded", False):
            self.dave_downgraded = False
            if self.dave_session:
                self.dave_session.set_passthrough_mode(False, 10)
            _log.debug('DAVE Session upgraded')

        _log.debug('Transition id %d executed', transition_id)

    d_vs.VoiceConnectionState._execute_transition = patched_execute_transition

    orig_connect_ws = d_vs.VoiceConnectionState._connect_websocket

    async def patched_connect_ws(self, resume: bool):
        if not resume and hasattr(self, "connected_user_ids"):
            self.connected_user_ids.clear()
        return await orig_connect_ws(self, resume)

    d_vs.VoiceConnectionState._connect_websocket = patched_connect_ws

    # 2. Patch DiscordVoiceWebSocket.received_message
    orig_received_message = d_gw.DiscordVoiceWebSocket.received_message

    async def patched_received_message(self, msg: Dict[str, Any]) -> None:
        op = msg.get('op')
        data = msg.get('d')
        state = self._connection

        if op == 11:  # CLIENTS_CONNECT
            if not hasattr(state, "connected_user_ids"):
                state.connected_user_ids = set()
            if isinstance(data, dict) and 'user_ids' in data:
                state.connected_user_ids.update(int(uid) for uid in data['user_ids'])
            return await orig_received_message(self, msg)

        if op == 13:  # CLIENT_DISCONNECT
            if not hasattr(state, "connected_user_ids"):
                state.connected_user_ids = set()
            if isinstance(data, dict) and 'user_id' in data:
                state.connected_user_ids.discard(int(data['user_id']))
            return await orig_received_message(self, msg)

        if state.dave_session and op == d_gw.DiscordVoiceWebSocket.DAVE_PREPARE_TRANSITION:
            _log.debug(
                'Preparing for DAVE transition id %d for protocol version %d',
                data['transition_id'],
                data['protocol_version'],
            )
            state.dave_pending_transitions[data['transition_id']] = data['protocol_version']
            try:
                state.dave_session.prepare_transition(data['transition_id'], data['protocol_version'])
            except Exception:
                _log.exception('Failed to prepare DAVE transition id %d', data['transition_id'])

            if data['protocol_version'] == 0:
                state.dave_session.set_passthrough_mode(True)

            if data['transition_id'] == 0:
                await state._execute_transition(data['transition_id'])
            else:
                await self.send_transition_ready(data['transition_id'])
            return

        return await orig_received_message(self, msg)

    d_gw.DiscordVoiceWebSocket.received_message = patched_received_message

    # 3. Patch DiscordVoiceWebSocket.received_binary_message
    orig_received_binary = d_gw.DiscordVoiceWebSocket.received_binary_message

    async def patched_received_binary_message(self, msg: bytes) -> None:
        self.seq_ack = struct.unpack_from('>H', msg, 0)[0]
        op = msg[2]
        state = self._connection

        if state.dave_session is None:
            return

        if not hasattr(state, "connected_user_ids"):
            state.connected_user_ids = set()

        if op == self.MLS_PROPOSALS:
            optype = msg[3]
            result = state.dave_session.process_proposals(
                davey.ProposalsOperationType.append if optype == 0 else davey.ProposalsOperationType.revoke,
                msg[4:],
                [*state.connected_user_ids, state.user.id],
            )
            if isinstance(result, davey.CommitWelcome):
                await self.send_binary(
                    d_gw.DiscordVoiceWebSocket.MLS_COMMIT_WELCOME,
                    result.commit + result.welcome if result.welcome else result.commit,
                )
            _log.debug('MLS proposals processed')
            return

        if op == self.MLS_ANNOUNCE_COMMIT_TRANSITION:
            transition_id = struct.unpack_from('>H', msg, 3)[0]
            try:
                if not state.dave_session.process_commit(msg[5:]):
                    _log.debug('MLS commit ignored for transition id %d', transition_id)
                    return
                state.dave_session.prepare_transition(transition_id, state.dave_session.protocol_version)
                if transition_id != 0:
                    state.dave_pending_transitions[transition_id] = state.dave_protocol_version
                    await self.send_transition_ready(transition_id)
                _log.debug('MLS commit processed for transition id %d', transition_id)
            except Exception:
                await state._recover_from_invalid_commit(transition_id)
            return

        if op == self.MLS_WELCOME:
            transition_id = struct.unpack_from('>H', msg, 3)[0]
            try:
                state.dave_session.process_welcome(msg[5:], [*state.connected_user_ids, state.user.id])
                state.dave_session.prepare_transition(transition_id, state.dave_session.protocol_version)
                if transition_id != 0:
                    state.dave_pending_transitions[transition_id] = state.dave_protocol_version
                    await self.send_transition_ready(transition_id)
                _log.debug('MLS welcome processed for transition id %d', transition_id)
            except Exception:
                await state._recover_from_invalid_commit(transition_id)
            return

        return await orig_received_binary(self, msg)

    d_gw.DiscordVoiceWebSocket.received_binary_message = patched_received_binary_message

    # 4. Patch VoiceClient._get_voice_packet & send_audio_packet
    def patched_get_voice_packet(self, data: bytes):
        if self._connection.dave_session and self._connection.can_encrypt:
            if not self._connection.dave_session.can_encrypt:
                return None
            packet = self._connection.dave_session.encrypt_opus(data)
        else:
            packet = data

        header = bytearray(12)
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into('>H', header, 2, self.sequence)
        struct.pack_into('>I', header, 4, self.timestamp)
        struct.pack_into('>I', header, 8, self.ssrc)

        encrypt_packet = getattr(self, '_encrypt_' + self.mode)
        return encrypt_packet(header, packet)

    d_vc.VoiceClient._get_voice_packet = patched_get_voice_packet

    def patched_send_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
        self.checked_add('sequence', 1, 65535)
        if encode:
            encoded_data = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        if packet is None:
            return
        try:
            self._connection.send_packet(packet)
        except OSError:
            _log.debug('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)
        self.checked_add('timestamp', self.encoder.SAMPLES_PER_FRAME, 4294967295)

    d_vc.VoiceClient.send_audio_packet = patched_send_audio_packet


# Tự động kích hoạt khi import
apply_dave_patch()

