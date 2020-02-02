/*
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
 */

/*! Select2 4.0.0 | https://github.com/select2/select2/blob/master/LICENSE.md */

(function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;return e.define("select2/i18n/zh-TW",[],function(){return{inputTooLong:function(e){var t=e.input.length-e.maximum,n="請刪掉"+t+"個字元";return n},inputTooShort:function(e){var t=e.minimum-e.input.length,n="請再輸入"+t+"個字元";return n},loadingMore:function(){return"載入中…"},maximumSelected:function(e){var t="你只能選擇最多"+e.maximum+"項";return t},noResults:function(){return"沒有找到相符的項目"},searching:function(){return"搜尋中…"}}}),{define:e.define,require:e.require}})();