package com.pukaar.android.data.mesh

import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.VerificationStatus
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AlertVerificationService @Inject constructor() {
    fun verifyAlertSignature(alert: CycloneAlert): VerificationStatus {
        return if (alert.signature.isNotBlank()) VerificationStatus.VERIFIED else VerificationStatus.UNVERIFIED
    }

    fun verifyPayloadSignature(payload: String, signature: String, senderIdentity: String): Boolean {
        // For demo: valid if signature and senderIdentity are non-empty
        return signature.isNotBlank() && senderIdentity.isNotBlank()
    }
}
