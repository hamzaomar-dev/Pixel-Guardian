from PySide6.QtWidgets import QStackedWidget, QWidget


class PageRouter(QStackedWidget):
    """إدارة صفحات البرنامج والتنقل بينها."""

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("pageRouter")
        self._pages: dict[str, QWidget] = {}

    def add_page(
        self,
        page_name: str,
        page_widget: QWidget,
    ) -> None:
        """إضافة صفحة جديدة إلى الموجّه."""

        if page_name in self._pages:
            raise ValueError(
                f"Page already exists: {page_name}"
            )

        self._pages[page_name] = page_widget
        self.addWidget(page_widget)

    def show_page(
        self,
        page_name: str,
    ) -> bool:
        """عرض صفحة حسب اسمها."""

        page_widget = self._pages.get(page_name)

        if page_widget is None:
            return False

        self.setCurrentWidget(page_widget)
        return True

    def has_page(
        self,
        page_name: str,
    ) -> bool:
        """التحقق من وجود صفحة."""

        return page_name in self._pages

    def get_page(
        self,
        page_name: str,
    ) -> QWidget | None:
        """إرجاع الصفحة حسب اسمها."""

        return self._pages.get(page_name)