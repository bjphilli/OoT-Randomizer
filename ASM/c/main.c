#include "dungeon_info.h"
#include "file_select.h"
#include "get_items.h"
#include "models.h"
#include "gfx.h"
#include "text.h"
#include "util.h"
#include "quickboots.h"
#include "z64.h"

void c_init() {
    heap_init();
    gfx_init();
    text_init();
    quickboots_init();
    item_overrides_init();
    models_init();
}

void before_game_state_update() {
    give_pending_item();
    handle_quickboots();
}

void after_game_state_update() {
    z64_disp_buf_t *db = &(z64_ctxt.gfx->overlay);
    draw_dungeon_info(db);
    draw_quickboots(db);
}

void after_scene_init() {
    models_reset();
}
