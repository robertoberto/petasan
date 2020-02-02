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

(function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;return e.define("select2/i18n/he",[],function(){return{errorLoading:function(){return"התוצאות לא נטענו בהלכה"},inputTooLong:function(e){var t=e.input.length-e.maximum,n="נא למחוק "+t+" תווים";return t!=1&&(n+="s"),n},inputTooShort:function(e){var t=e.minimum-e.input.length,n="נא להכניס "+t+" תווים או יותר";return n},loadingMore:function(){return"טען תוצאות נוספות…"},maximumSelected:function(e){var t="באפשרותך לבחור רק "+e.maximum+" פריטים";return e.maximum!=1&&(t+="s"),t},noResults:function(){return"לא נמצאו תוצאות"},searching:function(){return"מחפש…"}}}),{define:e.define,require:e.require}})();