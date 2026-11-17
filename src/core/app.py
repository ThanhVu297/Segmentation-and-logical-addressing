"""Controller nghiệp vụ cho ứng dụng segmentation, không phụ thuộc GUI."""

from pathlib import Path

import pandas as pd

from .csv_input import STATUS_INVALID_INPUT, load_input_files
from .csv_output import write_steps_csv, write_trace_csv
from .result_types import Segment, SegmentTable, Status, Step, TranslationResult
from .translator import translate
from .validator import validate_table


class SegmentationController:
    def __init__(self, mem_size: int = 5000) -> None:
        if mem_size <= 0:
            raise ValueError("mem_size phải > 0")

        self.mem_size = mem_size
        self.segment_table = SegmentTable(mem_size=mem_size)
        self.segment_df = None
        self.address_df = None
        self._loaded = False

    def load_files(self, segments_path: str, addresses_path: str):
        """Đọc CSV, tạo bảng segment và validate bảng trước khi lưu trạng thái."""
        segment_df, address_df = load_input_files(
            segments_path,
            addresses_path,
        )

        table = SegmentTable(mem_size=self.mem_size)
        for row in segment_df.itertuples(index=False):
            table.add(
                Segment(
                    seg_id=int(row.seg_id),
                    base=int(row.base),
                    limit=int(row.limit),
                    perm=str(row.perm),
                )
            )

        issues = validate_table(table, self.mem_size)
        if issues:
            details = "\n".join(f"- {issue.message}" for issue in issues)
            raise ValueError(f"Segment table không hợp lệ:\n{details}")

        # Chỉ cập nhật dữ liệu hiện tại nếu toàn bộ bước nạp/validate thành công.
        self.segment_table = table
        self.segment_df = segment_df
        self.address_df = address_df
        self._loaded = True
        return segment_df, address_df

    def translate_one(self, seg_id, offset, access: str) -> TranslationResult:
        """Dịch một địa chỉ logic."""
        if not self._loaded:
            raise RuntimeError("Hãy nạp CSV trước khi dịch.")

        return translate(self.segment_table, seg_id, offset, access)

    def translate_batch(self) -> list[TranslationResult]:
        """Dịch các dòng addresses.csv; giữ lại dòng lỗi với trạng thái INVALID_INPUT."""
        if not self._loaded:
            raise RuntimeError("Hãy nạp CSV trước khi dịch.")

        results = []
        for row in self.address_df.itertuples(index=False):
            if row.status == STATUS_INVALID_INPUT:
                reason = f"Dòng {row.line}: {row.error}"
                results.append(
                    TranslationResult(
                        seg_id=self._to_none(row.seg_id),
                        offset=self._to_none(row.offset),
                        access=self._to_none(row.access),
                        status=Status.INVALID_INPUT,
                        reason=reason,
                        steps=[Step(reason, ok=False)],
                    )
                )
                continue

            results.append(
                translate(
                    self.segment_table,
                    int(row.seg_id),
                    int(row.offset),
                    str(row.access),
                )
            )

        return results

    def export_trace(
        self,
        results: list[TranslationResult],
        output_path: str | Path | None = None,
    ) -> tuple[Path, Path]:
        """Xuất trace tổng hợp và trace từng bước, trả về đường dẫn hai file."""
        trace_path = Path(write_trace_csv(results, output_path))
        steps_path = trace_path.with_name(f"{trace_path.stem}_steps.csv")
        write_steps_csv(results, steps_path)
        return trace_path, steps_path

    @staticmethod
    def _to_none(value):
        """Đổi giá trị thiếu của pandas thành None."""
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        return value
