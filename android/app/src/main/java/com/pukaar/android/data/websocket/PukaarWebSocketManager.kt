package com.pukaar.android.data.websocket

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.pukaar.android.data.api.dto.CycloneIntelligenceDto
import com.pukaar.android.data.api.dto.RiskZoneDto
import com.pukaar.android.data.api.mapper.toDomain
import com.pukaar.android.domain.repository.CycloneEvent
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.min
import kotlin.math.pow
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

enum class WsState {
    CONNECTING,
    CONNECTED,
    DISCONNECTED,
    FAILED
}

@Singleton
class PukaarWebSocketManager @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val gson: Gson
) {
    private val scope = CoroutineScope(Dispatchers.IO)
    private var webSocket: WebSocket? = null
    private var reconnectJob: Job? = null
    private var reconnectAttempts = 0
    private var currentUrl: String = "wss://pukaar.live/ws/events"
    private var isIntentionalClose = false

    private val _events = MutableSharedFlow<CycloneEvent>(
        replay = 0,
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<CycloneEvent> = _events.asSharedFlow()
    val eventsFlow: SharedFlow<CycloneEvent> get() = events

    private val _connectionState = MutableStateFlow(WsState.DISCONNECTED)
    val connectionState: StateFlow<WsState> = _connectionState.asStateFlow()

    fun connect(wsUrl: String = currentUrl) {
        currentUrl = wsUrl
        isIntentionalClose = false
        reconnectJob?.cancel()

        if (webSocket != null) return

        _connectionState.value = WsState.CONNECTING
        val request = Request.Builder().url(wsUrl).build()

        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _connectionState.value = WsState.CONNECTED
                reconnectAttempts = 0
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                scope.launch {
                    try {
                        val json: JsonObject = JsonParser.parseString(text).asJsonObject
                        val eventType = json.get("event")?.asString ?: json.get("type")?.asString
                        val dataElement = json.get("data")

                        when (eventType) {
                            "CYCLONE_DETECTED" -> {
                                val dto = gson.fromJson(dataElement, CycloneIntelligenceDto::class.java)
                                _events.emit(CycloneEvent.Detected(dto.toDomain()))
                            }
                            "CYCLONE_UPDATED" -> {
                                val dto = gson.fromJson(dataElement, CycloneIntelligenceDto::class.java)
                                _events.emit(CycloneEvent.Updated(dto.toDomain()))
                            }
                            "PREDICTION_UPDATED" -> {
                                val dto = gson.fromJson(dataElement, CycloneIntelligenceDto::class.java)
                                _events.emit(CycloneEvent.PredictionUpdated(dto.toDomain()))
                            }
                            "RISK_ZONES_UPDATED" -> {
                                val zoneDtos = gson.fromJson(dataElement, Array<RiskZoneDto>::class.java)
                                val zones = zoneDtos.map { it.toDomain() }
                                _events.emit(CycloneEvent.RiskUpdated(zones))
                            }
                        }
                    } catch (e: Exception) {
                        // Log parse exception
                    }
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionState.value = WsState.FAILED
                this@PukaarWebSocketManager.webSocket = null
                scheduleReconnect()
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _connectionState.value = WsState.DISCONNECTED
                this@PukaarWebSocketManager.webSocket = null
                if (!isIntentionalClose) {
                    scheduleReconnect()
                }
            }
        })
    }

    private fun scheduleReconnect() {
        if (isIntentionalClose) return
        reconnectJob?.cancel()
        reconnectJob = scope.launch {
            // Exponential backoff 1s -> 2s -> 4s -> 8s -> max 30s
            val backoffSeconds = min(30.0, 2.0.pow(reconnectAttempts.toDouble())).toLong()
            reconnectAttempts++
            delay(backoffSeconds * 1000)
            connect(currentUrl)
        }
    }

    fun disconnect() {
        isIntentionalClose = true
        reconnectJob?.cancel()
        webSocket?.close(1000, "Client initiated disconnect")
        webSocket = null
        _connectionState.value = WsState.DISCONNECTED
    }
}
