package com.pukaar.android.data.local.converters

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.PathPoint

class PukaarTypeConverters {
    private val gson = Gson()

    @TypeConverter
    fun fromStringList(value: List<String>?): String {
        return gson.toJson(value ?: emptyList<String>())
    }

    @TypeConverter
    fun toStringList(value: String?): List<String> {
        if (value.isNullOrEmpty()) return emptyList()
        val type = object : TypeToken<List<String>>() {}.type
        return try {
            gson.fromJson(value, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    @TypeConverter
    fun fromLatLng(latLng: LatLng?): String {
        return if (latLng == null) "" else "${latLng.latitude},${latLng.longitude}"
    }

    @TypeConverter
    fun toLatLng(value: String?): LatLng? {
        if (value.isNullOrEmpty()) return null
        val parts = value.split(",")
        return if (parts.size == 2) {
            val lat = parts[0].toDoubleOrNull() ?: 0.0
            val lon = parts[1].toDoubleOrNull() ?: 0.0
            LatLng(lat, lon)
        } else null
    }

    @TypeConverter
    fun fromLatLngList(list: List<LatLng>?): String {
        return gson.toJson(list ?: emptyList<LatLng>())
    }

    @TypeConverter
    fun toLatLngList(value: String?): List<LatLng> {
        if (value.isNullOrEmpty()) return emptyList()
        val type = object : TypeToken<List<LatLng>>() {}.type
        return try {
            gson.fromJson(value, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    @TypeConverter
    fun fromPathPointList(list: List<PathPoint>?): String {
        return gson.toJson(list ?: emptyList<PathPoint>())
    }

    @TypeConverter
    fun toPathPointList(value: String?): List<PathPoint> {
        if (value.isNullOrEmpty()) return emptyList()
        val type = object : TypeToken<List<PathPoint>>() {}.type
        return try {
            gson.fromJson(value, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }
}
