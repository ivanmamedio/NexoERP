"""SQLAlchemy repository for report entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp.modules.reports.application.ports import ReportRepositoryPort
from erp.modules.reports.domain import Report
from erp.modules.reports.infrastructure.models import ReportModel


class SqlAlchemyReportRepository(ReportRepositoryPort):
    """SQLAlchemy repository for report entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, report: Report) -> None:
        model = ReportModel()
        model.report_type = report.report_type
        model.filter_params = report.filter_params
        model.file_path = report.file_path
        model.file_format = report.file_format
        model.file_size_bytes = report.file_size_bytes
        model.generated_at = report.generated_at
        model.generated_by_user_id = report.generated_by_user_id
        model.status = report.status
        model.error_message = report.error_message
        self._session.add(model)
        self._session.flush()
        report.id = model.id

    def get_by_id(self, report_id: int) -> Report | None:
        model = self._session.get(ReportModel, report_id)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_recent(self, limit: int = 50) -> list[Report]:
        stmt = select(ReportModel).order_by(ReportModel.generated_at.desc()).limit(limit)
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_domain(m) for m in models]

    @staticmethod
    def _model_to_domain(model: ReportModel) -> Report:
        report = Report(
            id=model.id,
            report_type=model.report_type,
            filter_params=model.filter_params,
            file_path=model.file_path,
            file_format=model.file_format,
            file_size_bytes=model.file_size_bytes,
            generated_at=model.generated_at,
            generated_by_user_id=model.generated_by_user_id,
            status=model.status,
            error_message=model.error_message,
        )
        return report