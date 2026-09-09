package com.pukaar.android.data.websocket

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.pukaar.android.data.api.dto.AlertDto
import com.pukaar.android.data.api.dto.CycloneDto
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

@Singleton
class PukaarWebSocketClient @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val gson: Gson
) {
    private var webSocket: WebSocket? = null
    private val scope = CoroutineScope(Dispatchers.IO)

    private val _events = MutableSharedFlow<PukaarWsEvent>(
        replay = 1,
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<PukaarWsEvent> = _events.asSharedFlow()

    fun connect(wsUrl: String = "wss://pukaar.live/ws/cyclone") {
        if (webSocket != null) return

        val request = Request.Builder().url(wsUrl).build()
        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                scope.launch { _events.emit(PukaarWsEvent.Connected) }
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                scope.launch {
                    try {
                        val json: JsonObject = JsonParser.parseString(text).asJsonObject
                        val type = json.get("type")?.asString ?: return@launch
                        val dataElement = json.get("data")

                        when (type) {
                            "CYCLONE_UPDATE" -> {
                                val dto = gson.fromJson(dataElement, CycloneDto::class.java)
                                _events.emit(PukaarWsEvent.CycloneUpdate(dto.toDomain()))
                            }
                            "ALERT_BROADCAST" -> {
                                val dto = gson.fromJson(dataElement, AlertDto::class.java)
                                _events.emit(PukaarWsEvent.AlertReceived(dto.toDomain()))
                            }
                        }
                    } catch (e: Exception) {
                        _events.emit(PukaarWsEvent.Error(e))
                    }
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                scope.launch { _events.emit(PukaarWsEvent.Error(t)) }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                scope.launch { _events.emit(PukaarWsEvent.Disconnected) }
                this@PukaarWebSocketClient.webSocket = null
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, "Client shutdown")
        webSocket = null
    }
}
