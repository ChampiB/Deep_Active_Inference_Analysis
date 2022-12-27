from enum import IntEnum


class InferenceAlgorithms(IntEnum):
    """
    An enumerations of all the inference algorithm supported by the temporal slice.
    """
    BELIEF_PROPAGATION = 0
    LOOPY_BELIEF_PROPAGATION = 1
    BACKPROPAGATION = 2
