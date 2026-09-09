package com.pukaar.android.di

import com.google.gson.Gson
import com.pukaar.android.BuildConfig
import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.websocket.PukaarWebSocketManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)

        if (BuildConfig.DEBUG) {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            builder.addInterceptor(logging)
        }

        return builder.build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, gson: Gson): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
    }

    @Provides
    @Singleton
    fun providePukaarApi(retrofit: Retrofit): PukaarApi {
        return retrofit.create(PukaarApi::class.java)
    }

    @Provides
    @Singleton
    fun providePukaarWebSocketManager(
        okHttpClient: OkHttpClient,
        gson: Gson
    ): PukaarWebSocketManager {
        return PukaarWebSocketManager(okHttpClient, gson)
    }
}
