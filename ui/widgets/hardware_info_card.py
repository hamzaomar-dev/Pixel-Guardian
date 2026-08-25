from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)


class HardwareInfoCard(QFrame):
    """بطاقة موحدة لعرض قسم من معلومات الجهاز."""

    def __init__(
        self,
        title: str,
        initial_text: str = "Reading information...",
    ) -> None:
        super().__init__()

        self.setObjectName("hardwareInfoCard")

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self._setup_ui(
            title=title,
            initial_text=initial_text,
        )

    def _setup_ui(
        self,
        title: str,
        initial_text: str,
    ) -> None:
        """إنشاء محتويات البطاقة."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        layout.setSpacing(12)

        # إبقاء جميع العناصر في أعلى البطاقة
        layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.title_label = QLabel(title)
        self.title_label.setObjectName(
            "hardwareCardTitle"
        )
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.content_label = QLabel(
            initial_text
        )
        self.content_label.setObjectName(
            "hardwareCardContent"
        )
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignLeft
        )
        self.content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.content_label)

        # المساحة الزائدة تبقى أسفل المحتوى
        layout.addStretch()

    def set_content(self, text: str) -> None:
        """تحديث محتوى البطاقة."""

        self.content_label.setText(text)
        self.content_label.adjustSize()

    def set_loading(self) -> None:
        """إظهار حالة التحميل."""

        self.content_label.setText(
            "Reading information..."
        )

    def set_error(
        self,
        message: str,
        error_code: str | None = None,
    ) -> None:
        """عرض خطأ داخل البطاقة."""

        error_text = (
            "Unable to read this information.\n\n"
            f"Reason: {message or 'Unknown error'}"
        )

        if error_code:
            error_text += (
                f"\nError Code: {error_code}"
            )

        self.content_label.setText(
            error_text
        )