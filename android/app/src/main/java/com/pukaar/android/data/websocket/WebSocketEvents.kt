package com.pukaar.android.data.websocket

import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.SosMessage

sealed class PukaarWsEvent {
    data class CycloneUpdate(val data: CycloneData) : PukaarWsEvent()
    data class AlertReceived(val alert: Alert) : PukaarWsEvent()
    data class SosDistressRelayed(val message: SosMessage) : PukaarWsEvent()
    data object Connected : PukaarWsEvent()
    data object Disconnected : PukaarWsEvent()
    data class Error(val throwable: Throwable) : PukaarWsEvent()
}
