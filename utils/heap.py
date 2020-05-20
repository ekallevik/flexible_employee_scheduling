from heapq import heappop, heappush


def pop_from_max_heap(h):

    # TODO: add docstring

    score, element = heappop(h)

    return -score, element


def push_to_max_heap(h, score, element):
    # all the scores are inverted to convert the heap to a max heap. The heap sorts on first
    # elements of the tuple

    heappush(h, (-score, element))
