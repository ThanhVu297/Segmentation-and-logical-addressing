
"""Dich dia chi logic sang dia chi vat ly theo co che phan doan."""

from .result_types import (
    ACCESS_TYPES,
    Status,
    Step,
    TranslationResult,
)


def translate(table, seg_id, offset, access):
    """Dich mot dia chi logic va luu cac buoc xu ly."""

    result = TranslationResult(
        seg_id=seg_id,
        offset=offset,
        access=access,
    )

    # Buoc 1: Kiem tra du lieu dau vao
    if type(seg_id) is not int or type(offset) is not int:
        result.status = Status.INVALID_INPUT
        result.reason = "seg_id va offset phai la so nguyen"
        result.steps.append(
            Step("Kiem tra dau vao: seg_id hoac offset khong hop le",
                 ok=False)
        )
        return result

    if not isinstance(access, str) or access not in ACCESS_TYPES:
        result.status = Status.INVALID_INPUT
        result.reason = "Kieu truy cap phai la R, W hoac X"
        result.steps.append(
            Step("Kiem tra dau vao: kieu truy cap khong hop le",
                 ok=False)
        )
        return result

    result.steps.append(Step("Kiem tra du lieu dau vao: hop le"))

    # Buoc 2: Tim segment
    segment = table.get(seg_id)

    if segment is None:
        result.status = Status.SEGMENT_FAULT
        result.reason = f"Khong tim thay segment {seg_id}"
        result.steps.append(
            Step(f"Tim segment {seg_id}: khong tim thay", ok=False)
        )
        return result

    base = segment.base
    limit = segment.limit
    perm = segment.perm

    result.base = base
    result.limit = limit

    result.steps.append(
        Step(
            f"Tim thay segment {seg_id}: "
            f"base={base}, limit={limit}, perm={perm}"
        )
    )

    # Buoc 3: Kiem tra offset
    if offset < 0 or offset >= limit:
        result.status = Status.OFFSET_OUT_OF_RANGE
        result.reason = (
            f"Offset {offset} nam ngoai gioi han "
            f"0 den {limit - 1}"
        )
        result.steps.append(
            Step(
                f"Kiem tra offset {offset} voi limit {limit}: loi",
                ok=False,
            )
        )
        return result

    result.steps.append(
        Step(f"Kiem tra offset {offset} voi limit {limit}: hop le")
    )

    # Buoc 4: Kiem tra quyen truy cap
    if not isinstance(perm, str) or len(perm) != len(ACCESS_TYPES):
        result.status = Status.INVALID_INPUT
        result.reason = "Cau hinh quyen cua segment khong hop le"
        result.steps.append(
            Step("Kiem tra cau hinh quyen: khong hop le", ok=False)
        )
        return result

    permission_index = ACCESS_TYPES.index(access)

    if perm[permission_index] != access:
        result.status = Status.PROTECTION_FAULT
        result.reason = f"Segment {seg_id} khong cho phep truy cap {access}"
        result.steps.append(
            Step(f"Kiem tra quyen {access}: bi tu choi", ok=False)
        )
        return result

    result.steps.append(Step(f"Kiem tra quyen {access}: duoc phep"))

    # Buoc 5: Tinh dia chi vat ly
    result.physical = base + offset
    result.status = Status.OK
    result.reason = ""

    result.steps.append(
        Step(f"Physical = {base} + {offset} = {result.physical}")
    )

    return result


def translate_many(table, list_addresses):
    """Dich nhieu dia chi theo thu tu dau vao."""

    results = []

    for address in list_addresses:
        try:
            if isinstance(address, dict):
                seg_id = address["seg_id"]
                offset = address["offset"]
                access = address["access"]

            elif isinstance(address, (tuple, list)) and len(address) == 3:
                seg_id, offset, access = address

            else:
                result = TranslationResult(
                    seg_id=None,
                    offset=None,
                    access=None,
                    status=Status.INVALID_INPUT,
                    reason="Moi dia chi phai la dict hoac bo 3 "
                           "(seg_id, offset, access)",
                    steps=[
                        Step("Kiem tra dinh dang dia chi: khong hop le",
                             ok=False)
                    ],
                )
                results.append(result)
                continue

            results.append(translate(table, seg_id, offset, access))

        except (KeyError, TypeError, ValueError):
            result = TranslationResult(
                seg_id=None,
                offset=None,
                access=None,
                status=Status.INVALID_INPUT,
                reason="Dia chi thieu truong hoac sai dinh dang",
                steps=[
                    Step("Doc du lieu dia chi: khong hop le", ok=False)
                ],
            )
            results.append(result)

    return results
