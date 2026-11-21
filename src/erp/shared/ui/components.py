"""Componentes UI reutilizáveis baseados no design system."""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


SummaryCardVariant = Literal["primary", "success", "warning", "danger", "info", "neutral"]
AlertCounterSeverity = Literal["critical", "warning", "info", "success"]


class SummaryCard(QFrame):
    """Card de resumo (KPI) com título e valor.

    Uso:
        card = SummaryCard("Vendas", "R$ 10.000,00", "success")
        card.update_value("R$ 12.500,00")
    """

    def __init__(
        self,
        title: str,
        value: str = "R$ 0,00",
        variant: SummaryCardVariant = "primary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        self.setProperty("variant", variant)
        self.setFixedHeight(90)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("SummaryCardTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("SummaryCardValue")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

    def update_value(self, value: str) -> None:
        self._value_label.setText(value)

    def update_title(self, title: str) -> None:
        self._title_label.setText(title)

    def set_variant(self, variant: SummaryCardVariant) -> None:
        self.setProperty("variant", variant)
        self.style().unpolish(self)
        self.style().polish(self)


class AlertCounter(QFrame):
    """Contador de alertas com título e valor numérico.

    Uso:
        counter = AlertCounter("Pagar Vencidas", "5", "critical")
        counter.update_value("3")
    """

    def __init__(
        self,
        title: str,
        value: str = "0",
        severity: AlertCounterSeverity = "info",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("AlertCounter")
        self.setProperty("severity", severity)
        self.setFixedHeight(80)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("AlertCounterTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("AlertCounterValue")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

    def update_value(self, value: str) -> None:
        self._value_label.setText(value)

    def update_title(self, title: str) -> None:
        self._title_label.setText(title)

    def set_severity(self, severity: AlertCounterSeverity) -> None:
        self.setProperty("severity", severity)
        self.style().unpolish(self)
        self.style().polish(self)