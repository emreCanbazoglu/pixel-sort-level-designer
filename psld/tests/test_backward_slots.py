from psld.backward_slots import generate_backward_place_order, verify_forward_remove_order


def test_backward_order_and_forward_verification_small_block() -> None:
    mask = [
        [True, True, True],
        [True, True, True],
        [True, True, True],
    ]
    backward = generate_backward_place_order(mask)
    forward = list(reversed(backward))
    verify_forward_remove_order(mask, forward)


def test_backward_order_and_forward_verification_hollow_square() -> None:
    mask = [
        [True, True, True, True, True],
        [True, False, False, False, True],
        [True, False, True, False, True],
        [True, False, False, False, True],
        [True, True, True, True, True],
    ]
    backward = generate_backward_place_order(mask)
    forward = list(reversed(backward))
    verify_forward_remove_order(mask, forward)

