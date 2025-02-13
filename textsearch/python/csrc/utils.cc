// textsearch/python/csrc/utils.cc
//
// Copyright (c)  2023  Xiaomi Corporation

#include "textsearch/python/csrc/utils.h"
#include "textsearch/csrc/utils.h"

namespace fasttextsearch {

static constexpr const char *kRowIdsToRowSplitsDoc = R"doc(
Convert row ids to row splits.

Args:
  row_ids:
    A 1-D contiguous array of dtype np.uint32 containing row ids.
  row_splits:
    Pre-allocated array of dtype np.uint32. Its shape is (num_rows+1,).
    On return it will contain the computed row splits.
)doc";

static constexpr const char *kGetNew2OldDoc = R"doc(
Returns an array mapping the new indexes to the old indexes.
Its dimension is the number of new indexes (i.e. the number of True in keep).

Args:
  keep:
    A 1-D contiguous array of dtype np.bool indicating whether to keep current
    element (True to keep, False to drop).

>>> from textsearch import get_new2old
>>> import numpy as np
>>> keep = np.array([0, 0, 1, 0, 1, 0, 1, 1], dtype=bool)
>>> get_new2old(keep)
array([2, 4, 6, 7], dtype=uint32)

)doc";

static void PybindRowIdsToRowSplits(py::module &m) {
  m.def(
      "row_ids_to_row_splits",
      [](py::array_t<uint32_t> row_ids,
         py::array_t<uint32_t> *row_splits) -> void {
        py::buffer_info row_ids_buf = row_ids.request();
        const uint32_t *p_row_ids =
            static_cast<const uint32_t *>(row_ids_buf.ptr);

        py::buffer_info row_splits_buf = row_splits->request();
        uint32_t *p_row_splits = static_cast<uint32_t *>(row_splits_buf.ptr);

        int32_t num_elems = row_ids_buf.size;
        int32_t num_rows = row_splits_buf.size - 1;

        RowIdsToRowSplits(num_elems, p_row_ids, num_rows, p_row_splits);
      },
      py::arg("row_ids"), py::arg("row_splits"), kRowIdsToRowSplitsDoc);
}

static void PybindGetNew2Old(py::module &m) {
  m.def(
      "get_new2old",
      [](py::array_t<bool> keep) -> py::array_t<uint32_t> {
        py::buffer_info keep_buf = keep.request();
        size_t num_old_elems = keep_buf.size;
        const bool *p_keep = static_cast<const bool *>(keep_buf.ptr);
        std::vector<uint32_t> new2old;
        GetNew2Old(p_keep, num_old_elems, &new2old);
        return py::array(new2old.size(), new2old.data());
      },
      py::arg("keep"), kGetNew2OldDoc);
}

void PybindUtils(py::module &m) {
  PybindGetNew2Old(m);
  PybindRowIdsToRowSplits(m);
}

} // namespace fasttextsearch
