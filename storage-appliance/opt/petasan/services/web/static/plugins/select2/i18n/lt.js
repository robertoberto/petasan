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

(function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;return e.define("select2/i18n/lt",[],function(){function e(e,t,n,r){return e%100>9&&e%100<21||e%10===0?e%10>1?n:r:t}return{inputTooLong:function(t){var n=t.input.length-t.maximum,r="Pašalinkite "+n+" simbol";return r+=e(n,"ių","ius","į"),r},inputTooShort:function(t){var n=t.minimum-t.input.length,r="Įrašykite dar "+n+" simbol";return r+=e(n,"ių","ius","į"),r},loadingMore:function(){return"Kraunama daugiau rezultatų…"},maximumSelected:function(t){var n="Jūs galite pasirinkti tik "+t.maximum+" element";return n+=e(t.maximum,"ų","us","ą"),n},noResults:function(){return"Atitikmenų nerasta"},searching:function(){return"Ieškoma…"}}}),{define:e.define,require:e.require}})();