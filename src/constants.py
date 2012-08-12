# -*- coding: utf-8 -*-

MAX_COUNT = 4

#modes
EXPORT_MODES = (SUBDIR,
               DUPLICATE) = range(2)

#tree model columns
(COLUMN_NAME,
 COLUMN_STATE,
 COLUMN_URL) = range(3)

#states
STATES = (NONE, PAUSED, FINISHED,
          EXPORTED) = ("None", "Paused",
                       "Finished", "Exported")
