package com.pukaar.android.ui.screens.sos.inbox

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.usecase.GetSosInboxUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

@HiltViewModel
class SosInboxViewModel @Inject constructor(
    private val getSosInboxUseCase: GetSosInboxUseCase
) : ViewModel() {

    val inbox: StateFlow<List<SosMessage>> = getSosInboxUseCase()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )
}
