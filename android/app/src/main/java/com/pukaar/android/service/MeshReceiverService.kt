package com.pukaar.android.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.pukaar.android.MainActivity
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.dao.SeenPacketDao
import com.pukaar.android.data.mesh.BluetoothMeshReceiver
import com.pukaar.android.data.mesh.MeshPacketProcessor
import com.pukaar.android.data.mesh.WifiAwareMeshReceiver
import com.pukaar.android.domain.repository.MeshRepository
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.merge
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class MeshReceiverService : Service() {

    @Inject
    lateinit var processor: MeshPacketProcessor

    @Inject
    lateinit var seenPacketDao: SeenPacketDao

    @Inject
    lateinit var incomingSosDao: IncomingSosDao

    @Inject
    lateinit var meshRepository: MeshRepository

    companion object {
        const val NOTIFICATION_CHANNEL_ID = "pukaar_mesh"
        const val NOTIFICATION_ID = 1001
        const val SOS_NOTIFICATION_CHANNEL_ID = "pukaar_sos_receive"

        fun start(context: Context) {
            val intent = Intent(context, MeshReceiverService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            val intent = Intent(context, MeshReceiverService::class.java)
            context.stopService(intent)
        }
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var btReceiver: BluetoothMeshReceiver? = null
    private var wifiReceiver: WifiAwareMeshReceiver? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
        startForeground(NOTIFICATION_ID, buildPersistentNotification())
        startMeshListeners()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    private fun startMeshListeners() {
        btReceiver = BluetoothMeshReceiver(this)
        wifiReceiver = WifiAwareMeshReceiver(this)

        serviceScope.launch {
            merge(btReceiver!!.incomingPackets, wifiReceiver!!.incomingPackets)
                .collect { (packet, transport) ->
                    processor.process(packet, transport)
                }
        }

        btReceiver?.start()
        wifiReceiver?.start()
    }

    private fun buildPersistentNotification(): Notification {
        val launchIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("PUKAAR Mesh Active")
            .setContentText("Listening for emergency distress signals")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .build()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java) ?: return

            // Channel 1: MESH — LOW importance, persistent background notification
            val meshChannel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "Mesh Network Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps peer-to-peer offline mesh receiver active in the background"
                setShowBadge(false)
            }

            // Channel 2: SOS_RECEIVE — HIGH importance, sound on, vibrate on, for incoming SOS alerts
            val soundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            val audioAttributes = AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .setUsage(AudioAttributes.USAGE_ALARM)
                .build()

            val sosChannel = NotificationChannel(
                SOS_NOTIFICATION_CHANNEL_ID,
                "Emergency SOS Signals",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Critical alerts when emergency SOS distress packets are received from nearby peers"
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 500, 200, 500)
                setSound(soundUri, audioAttributes)
                setShowBadge(true)
            }

            manager.createNotificationChannel(meshChannel)
            manager.createNotificationChannel(sosChannel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        serviceScope.cancel()
        btReceiver?.stop()
        wifiReceiver?.stop()
        super.onDestroy()
    }
}
