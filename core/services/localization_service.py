from __future__ import annotations

from core.services.application_settings_service import (
    ApplicationSettingsService,
)


class LocalizationService:
    """إدارة لغة وترجمة واجهة Pixel Guardian."""

    SUPPORTED_LANGUAGES = (
        "en",
        "ar",
    )

    TRANSLATIONS = {
        "en": {
            "app_name": "Pixel Guardian",

            # Navigation
            "dashboard": "Dashboard",
            "hardware_information": "Hardware Information",
            "disk_health": "Disk Health",
            "live_monitor": "Live Monitor",
            "drivers": "Drivers",
            "cleaner": "Cleaner",
            "game_lab": "Game Lab",
            "settings": "Settings",
            "about": "About",

            # Common
            "save": "Save",
            "cancel": "Cancel",
            "close": "Close",
            "refresh": "Refresh",
            "scan": "Scan",
            "enabled": "Enabled",
            "disabled": "Disabled",
            "available": "Available",
            "unavailable": "Unavailable",

            # Settings
            "settings_title": "Settings",
            "settings_subtitle": (
                "Customize Pixel Guardian according "
                "to your preferences."
            ),
            "general": "General",
            "language": "Language",
            "language_description": (
                "Choose the language used by "
                "Pixel Guardian."
            ),
            "english": "English",
            "arabic": "Arabic",

            "appearance": "Appearance",
            "theme": "Theme",
            "theme_description": (
                "Choose the application appearance."
            ),
            "dark": "Dark",
            "light": "Light",
            "system": "Use System Setting",

            "notifications": "Notifications",
            "notifications_enabled": (
                "Enable Windows notifications"
            ),
            "notifications_description": (
                "Show notifications when scans and "
                "maintenance operations finish."
            ),
            "notification_sound": (
                "Play notification sounds"
            ),
            "minimize_to_tray": (
                "Minimize Pixel Guardian to system tray"
            ),
            "start_minimized": (
                "Start Pixel Guardian minimized"
            ),

            "automatic_scanning": "Automatic Scanning",
            "live_monitoring": "Live Monitoring",
            "gaming_performance": "Gaming Performance",
            "maintenance_safety": (
                "Maintenance and Safety"
            ),
            "application_data": "Application Data",

            "save_settings": "Save Settings",
            "restore_defaults": "Restore Defaults",
            "settings_saved": (
                "Settings saved successfully."
            ),
            "restart_required": (
                "Restart Pixel Guardian to apply "
                "the selected language."
            ),
        },

        "ar": {
            "app_name": "بيكسل جارديان",

            # Navigation
            "dashboard": "لوحة التحكم",
            "hardware_information": "معلومات الجهاز",
            "disk_health": "صحة الأقراص",
            "live_monitor": "المراقبة المباشرة",
            "drivers": "التعريفات",
            "cleaner": "تنظيف الجهاز",
            "game_lab": "مختبر الألعاب",
            "settings": "الإعدادات",
            "about": "حول البرنامج",

            # Common
            "save": "حفظ",
            "cancel": "إلغاء",
            "close": "إغلاق",
            "refresh": "تحديث",
            "scan": "فحص",
            "enabled": "مفعّل",
            "disabled": "متوقف",
            "available": "متوفر",
            "unavailable": "غير متوفر",

            # Settings
            "settings_title": "الإعدادات",
            "settings_subtitle": (
                "خصص بيكسل جارديان حسب تفضيلاتك."
            ),
            "general": "عام",
            "language": "اللغة",
            "language_description": (
                "اختر اللغة المستخدمة داخل "
                "بيكسل جارديان."
            ),
            "english": "الإنجليزية",
            "arabic": "العربية",

            "appearance": "المظهر",
            "theme": "الثيم",
            "theme_description": (
                "اختر مظهر واجهة البرنامج."
            ),
            "dark": "داكن",
            "light": "فاتح",
            "system": "استخدام إعداد النظام",

            "notifications": "الإشعارات",
            "notifications_enabled": (
                "تشغيل إشعارات ويندوز"
            ),
            "notifications_description": (
                "عرض إشعار عند انتهاء الفحوصات "
                "وعمليات الصيانة."
            ),
            "notification_sound": (
                "تشغيل صوت الإشعارات"
            ),
            "minimize_to_tray": (
                "تصغير بيكسل جارديان بجانب الساعة"
            ),
            "start_minimized": (
                "تشغيل بيكسل جارديان مصغرًا"
            ),

            "automatic_scanning": "الفحص التلقائي",
            "live_monitoring": "المراقبة المباشرة",
            "gaming_performance": "أداء الألعاب",
            "maintenance_safety": (
                "الصيانة والأمان"
            ),
            "application_data": "بيانات البرنامج",

            "save_settings": "حفظ الإعدادات",
            "restore_defaults": (
                "استعادة الإعدادات الافتراضية"
            ),
            "settings_saved": (
                "تم حفظ الإعدادات بنجاح."
            ),
            "restart_required": (
                "أعد تشغيل بيكسل جارديان "
                "لتطبيق اللغة المختارة."
            ),
        },
    }

    def __init__(
        self,
        language: str | None = None,
        settings_service: (
            ApplicationSettingsService | None
        ) = None,
    ) -> None:
        self._settings_service = (
            settings_service
            or ApplicationSettingsService()
        )

        selected_language = (
            language
            if language is not None
            else self._settings_service.language
        )

        self._language = self._normalize_language(
            selected_language
        )

    @property
    def language(self) -> str:
        """رمز اللغة الحالية."""

        return self._language

    @property
    def is_rtl(self) -> bool:
        """هل اتجاه اللغة من اليمين إلى اليسار؟"""

        return self._language == "ar"

    def set_language(
        self,
        language: str,
        save: bool = True,
    ) -> None:
        """تغيير اللغة الحالية."""

        normalized_language = (
            self._normalize_language(
                language
            )
        )

        self._language = normalized_language

        if save:
            self._settings_service.language = (
                normalized_language
            )

    def translate(
        self,
        key: str,
        **format_values,
    ) -> str:
        """ترجمة مفتاح نصي إلى اللغة الحالية."""

        normalized_key = str(
            key or ""
        ).strip()

        if not normalized_key:
            return ""

        language_values = (
            self.TRANSLATIONS.get(
                self._language,
                {},
            )
        )

        english_values = (
            self.TRANSLATIONS["en"]
        )

        translated_value = (
            language_values.get(
                normalized_key
            )
            or english_values.get(
                normalized_key
            )
            or normalized_key
        )

        if not format_values:
            return translated_value

        try:
            return translated_value.format(
                **format_values
            )

        except (
            KeyError,
            ValueError,
        ):
            return translated_value

    def tr(
        self,
        key: str,
        **format_values,
    ) -> str:
        """اختصار لدالة translate."""

        return self.translate(
            key,
            **format_values,
        )

    @classmethod
    def _normalize_language(
        cls,
        language: str,
    ) -> str:
        """تنظيف رمز اللغة والتحقق منه."""

        normalized_language = str(
            language or ""
        ).strip().casefold()

        if normalized_language not in (
            cls.SUPPORTED_LANGUAGES
        ):
            return "en"

        return normalized_language