package com.chakravyuh.android.data.websocket

import com.chakravyuh.android.data.api.dto.AlertDto
import com.chakravyuh.android.data.api.dto.CycloneDto
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
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
class ChakravyuhWebSocketClient @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val gson: Gson
) {
    private var webSocket: WebSocket? = null
    private val scope = CoroutineScope(Dispatchers.IO)

    private val _events = MutableSharedFlow<WebSocketEvent>(
        replay = 1,
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<WebSocketEvent> = _events.asSharedFlow()

    fun connect(wsUrl: String = "wss://chakravyuh.live/ws/stream") {
        if (webSocket != null) return

        val request = Request.Builder().url(wsUrl).build()
        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                scope.launch { _events.emit(WebSocketEvent.Connected) }
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
                                _events.emit(WebSocketEvent.CycloneUpdate(dto.toDomain()))
                            }
                            "ALERT_EMITTED" -> {
                                val dto = gson.fromJson(dataElement, AlertDto::class.java)
                                _events.emit(WebSocketEvent.NewAlert(dto.toDomain()))
                            }
                            "SOS_BROADCAST" -> {
                                val sosId = json.get("sos_id")?.asString ?: ""
                                val lat = json.get("lat")?.asDouble ?: 0.0
                                val lon = json.get("lon")?.asDouble ?: 0.0
                                _events.emit(WebSocketEvent.SosBroadcast(sosId, lat, lon))
                            }
                        }
                    } catch (e: Exception) {
                        _events.emit(WebSocketEvent.Error(e))
                    }
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                scope.launch { _events.emit(WebSocketEvent.Error(t)) }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                scope.launch { _events.emit(WebSocketEvent.Disconnected) }
                this@ChakravyuhWebSocketClient.webSocket = null
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
    }

    fun sendMessage(text: String): Boolean {
        return webSocket?.send(text) ?: false
    }
}
