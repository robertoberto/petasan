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

(function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;return e.define("select2/i18n/et",[],function(){return{inputTooLong:function(e){var t=e.input.length-e.maximum,n="Sisesta "+t+" täht";return t!=1&&(n+="e"),n+=" vähem",n},inputTooShort:function(e){var t=e.minimum-e.input.length,n="Sisesta "+t+" täht";return t!=1&&(n+="e"),n+=" rohkem",n},loadingMore:function(){return"Laen tulemusi…"},maximumSelected:function(e){var t="Saad vaid "+e.maximum+" tulemus";return e.maximum==1?t+="e":t+="t",t+=" valida",t},noResults:function(){return"Tulemused puuduvad"},searching:function(){return"Otsin…"}}}),{define:e.define,require:e.require}})();