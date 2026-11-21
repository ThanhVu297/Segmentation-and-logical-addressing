"""Dịch địa chỉ logic sang địa chỉ vật lý theo cơ chế phân đoạn.

Thứ tự xử lý của translate():
  0. Kiểm tra kiểu dữ liệu đầu vào (seg_id, offset là int; access là R/W/X).
     Sai -> INVALID_INPUT, chưa tra bảng segment.
  1-3. Gọi protection.check_fault (TV3): SEGMENT_FAULT -> OFFSET_OUT_OF_RANGE
     -> PROTECTION_FAULT. Đây là nơi duy nhất quyết định lỗi logic.
  4. Hợp lệ: physical = base + offset.

translate() chỉ dựng danh sách Step từ kết quả của check_fault.
"""

from .protection import check_fault
from .result_types import (
    ACCESS_TYPES,
    Status,
    Step,
    TranslationResult,
)


def translate(table, seg_id, offset, access):
    """Dịch một địa chỉ logic và lưu các bước xử lý."""

    result = TranslationResult(
        seg_id=seg_id,
        offset=offset,
        access=access,
    )

    # Bước 0: kiểm tra kiểu dữ liệu (check_fault giả định kiểu đã đúng)
    if type(seg_id) is not int or type(offset) is not int:
        result.status = Status.INVALID_INPUT
        result.reason = "seg_id và offset phải là số nguyên"
        result.steps.append(
            Step("Kiểm tra đầu vào: seg_id hoặc offset không hợp lệ",
                 ok=False)
        )
        return result

    if not isinstance(access, str) or access not in ACCESS_TYPES:
        result.status = Status.INVALID_INPUT
        result.reason = "Kiểu truy cập phải là R, W hoặc X"
        result.steps.append(
            Step("Kiểm tra đầu vào: kiểu truy cập không hợp lệ", ok=False)
        )
        return result

    result.steps.append(Step("Kiểm tra dữ liệu đầu vào: hợp lệ"))

    # Bước 1-3: mọi quyết định lỗi nằm ở protection.check_fault
    fault = check_fault(table, seg_id, offset, access)
    result.status = fault.status
    result.reason = fault.reason

    if fault.status == Status.SEGMENT_FAULT:
        result.steps.append(
            Step(f"Tìm segment {seg_id}: không tìm thấy", ok=False)
        )
        return result

    segment = table.get(seg_id)
    base = segment.base
    limit = segment.limit
    perm = segment.perm

    result.base = base
    result.limit = limit
    result.steps.append(
        Step(
            f"Tìm thấy segment {seg_id}: "
            f"base={base}, limit={limit}, perm={perm}"
        )
    )

    if fault.status == Status.OFFSET_OUT_OF_RANGE:
        result.steps.append(
            Step(f"Kiểm tra offset {offset} với limit {limit}: lỗi",
                 ok=False)
        )
        return result

    result.steps.append(
        Step(f"Kiểm tra offset {offset} với limit {limit}: hợp lệ")
    )

    if fault.status == Status.PROTECTION_FAULT:
        result.steps.append(
            Step(f"Kiểm tra quyền {access} với perm {perm}: bị từ chối",
                 ok=False)
        )
        return result

    result.steps.append(
        Step(f"Kiểm tra quyền {access} với perm {perm}: được phép")
    )

    # Bước 4: tính địa chỉ vật lý
    result.physical = base + offset
    result.steps.append(
        Step(f"Physical = {base} + {offset} = {result.physical}")
    )

    return result


def _invalid_address(reason, step_description, seg_id=None, offset=None,
                     access=None):
    """Tạo kết quả INVALID_INPUT cho một phần tử địa chỉ không đọc được."""
    return TranslationResult(
        seg_id=seg_id,
        offset=offset,
        access=access,
        status=Status.INVALID_INPUT,
        reason=reason,
        steps=[Step(step_description, ok=False)],
    )


def translate_many(table, list_addresses):
    """Dịch nhiều địa chỉ theo thứ tự đầu vào.

    Phần tử sai định dạng cho ra INVALID_INPUT (kèm lý do cụ thể) và
    không làm dừng các phần tử còn lại.
    """

    results = []

    for index, address in enumerate(list_addresses, start=1):
        label = f"Địa chỉ thứ {index}"

        if isinstance(address, dict):
            missing = [key for key in ("seg_id", "offset", "access")
                       if key not in address]
            if missing:
                results.append(_invalid_address(
                    f"{label} thiếu trường: {', '.join(missing)}",
                    f"Đọc dữ liệu địa chỉ: thiếu {', '.join(missing)}",
                    address.get("seg_id"),
                    address.get("offset"),
                    address.get("access"),
                ))
                continue
            seg_id = address["seg_id"]
            offset = address["offset"]
            access = address["access"]

        elif isinstance(address, (tuple, list)) and len(address) == 3:
            seg_id, offset, access = address

        else:
            results.append(_invalid_address(
                f"{label} phải là dict hoặc bộ 3 (seg_id, offset, access)",
                "Kiểm tra định dạng địa chỉ: không hợp lệ",
            ))
            continue

        try:
            results.append(translate(table, seg_id, offset, access))
        except (TypeError, ValueError, AttributeError) as error:
            # Lỗi bất ngờ từ bảng segment hoặc dữ liệu segment, không phải
            # lỗi do địa chỉ: nêu rõ loại lỗi để dễ tìm nguyên nhân.
            results.append(_invalid_address(
                f"{label}: lỗi khi dịch ({type(error).__name__}: {error})",
                "Dịch địa chỉ: gặp lỗi ngoài dự kiến",
                seg_id, offset, access,
            ))

    return results
