# Copyright      2023   Xiaomi Corp.       (author: Wei Kang)
#
# See ../../../LICENSE for clarification regarding multiple authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import _fasttextsearch
import numpy as np


def _renumbering(array: np.ndarray) -> np.ndarray:
    """Renumber element in the input array such that the returned array
    contains entries ranging from 0 to M - 1, where M equals
    to number of unique entries in the input array.

    The order of entries in the output array is the same as the order
    of entries in the input array. That is, if array[i] < array[j], then
    ans[i] < ans[j].

    Args:
      array:
        A 1-D array.
    Returns:
      Return a renumbered 1-D array.
    """
    uniqued, inverse = np.unique(array, return_inverse=True)
    # Note: uniqued[inverse] == array

    if uniqued.size < np.iinfo(np.uint8).max:
        ans_dtype = np.uint8
    elif uniqued.size < np.iinfo(np.uint32).max:
        ans_dtype = np.uint32
    else:
        # unlikely
        ans_dtype = np.int64

    indexes_sorted2unsorted = np.argsort(uniqued)
    indexes_unsorted2sorted = np.empty((uniqued.size), dtype=ans_dtype)
    indexes_unsorted2sorted[indexes_sorted2unsorted] = np.arange(uniqued.size)

    return indexes_unsorted2sorted[inverse]


def create_suffix_array(
    array: np.ndarray,
    enable_renumbering: bool = True,
) -> np.ndarray:
    """Create a suffix array from a 1-D input array.

    hint:
      Please refer to https://en.wikipedia.org/wiki/Suffix_array
      for what suffix array is. Different from the above Wikipedia
      article the special sentinel letter ``$`` in fasttextsearch
      is known as EOS and it is larger than any other characters.

    Args:
      array:
        A 1-D integer (or unsigned integer) array of shape (seq_len,).
        Note: Inside this function, we will append explicitly an EOS
        symbol that is larger than ``array.max()``.
      enable_renumbering:
        True to enable renumbering before computing the suffix array.
    Returns:
      Returns a suffix array of type np.int64, of shape (seq_len,).
      This will consist of some permutation of the elements
      ``0 .. seq_len - 1``.
    """
    assert array.ndim == 1, array.ndim

    if enable_renumbering:
        array = _renumbering(array)

    max_symbol = array.max()
    assert max_symbol < np.iinfo(array.dtype).max - 1, max_symbol
    eos = max_symbol + 1
    padding = np.array([eos, 0, 0, 0], dtype=array.dtype)

    padded_array = np.concatenate([array, padding])

    # The C++ code requires the input array to be contiguous.
    array_int64 = np.ascontiguousarray(padded_array, dtype=np.int64)
    return _fasttextsearch.create_suffix_array(array_int64)


def find_close_matches(suffix_array: np.ndarray, query_len: int) -> np.ndarray:
    """
    Assuming the suffix array was created from a text where the first `query_len`
    positions represent the query text and the remaining positions represent
    the reference text, return a list indicating, for each suffix position in the query
    text, the two suffix positions in the reference text that immediately precede and
    follow it lexicographically.  (I think suffix position refers to the last character
    of a suffix).     This is easy to do from the suffix array without computing,
    for example, the LCP array; and it produces exactly 2 matches per position in the
    query text, which is also convenient.

    (Note: the query and reference texts could each represent multiple separate
    sequences, but that is handled by other code; class SourcedText keeps track of that
    information.)

    Args:
     suffix_array: A suffix array as created by create_suffix_array(), of dtype
        np.int64 and shape (seq_len,).

      query_len: A number 0 <= query_len < seq_len, indicating the length in symbols
       (likely bytes) of the query part of the text that was used to create `suffix_array`.

    Returns an np.ndarray of shape (query_len * 2,), of the same dtype as suffix_array,
      in which positions 2*i and 2*i + 1 represent the two positions in the original
      text that are within the reference portion, and which immediately follow and
      precede, in the suffix array, query position i.  This means that the
      suffixes ending at those positions are reverse-lexicographically close
      to the suffix ending at position i.  As a special case, if one of these
      returned numbers would equal the EOS position (position seq_len - 1), or
      if a query position is before any reference position in the suffix aray, we
      output seq_len - 2 instead to avoid having to handle special cases later on
      (anyway, these would not represent a close match).
    """
    assert query_len >= 0, query_len
    assert suffix_array.ndim == 1, suffix_array.ndim
    assert suffix_array.dtype == np.int64, suffix_array.dtype
    seq_len = suffix_array.size
    assert query_len < seq_len, (query_len, seq_len)

    output = np.empty(query_len * 2, dtype=suffix_array.dtype)

    last_pos = -1
    for i in range(seq_len):
        text_pos = suffix_array[i]
        if text_pos >= query_len:
            for j in range(last_pos + 1, i):
                query_pos = suffix_array[j]
                if query_pos < query_len:
                    pre_ref_pos = (
                        seq_len - 2 if last_pos == -1 else suffix_array[last_pos]
                    )
                    output[2 * query_pos] = pre_ref_pos
                    output[2 * query_pos + 1] = text_pos
            last_pos = i
    return output
