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

var global_schedule = {};

function get_text(schedule) {

    var text = "";

    var week_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    if (schedule.type == 'daily') {

        text += "Daily";

        $('#daily').prop('checked', true);

        $('#daily_form').show();

        onChangeDailyForm('daily_at_val');

        select_at_val(schedule.at, 'daily_at_val');

        if (schedule.every > -1) {

            if(schedule.every == 1){

                text += " every " + schedule.every + " Hour";

            }else{
                text += " every " + schedule.every + " " + schedule.unit;
            }

            $('#daily_every').prop('checked', true);
            $('#daily_every_type').prop('disabled', false);
            $('#daily_every_val_hour').prop('disabled', false);
            $('#daily_every_val_minute').prop('disabled', false);

            if (schedule.unit == "hours") {



                $('#daily_every_type').val('hours');

                $('#daily_every_val_hour').val(schedule.every);

            } else {

                $('#daily_every_val_hour').hide();



                $('#daily_every_type').val('minutes');

                $('#daily_every_val_minute').val(schedule.every);

                $('#daily_every_val_minute').show();


            }

        } else {

            $('#daily_at_val').prop('disabled', false);

            $('#daily_at').prop('checked', true);

            if (schedule.at < 10) {

                text += " at 0" + schedule.at + ":00";

            } else {

                text += " at " + schedule.at + ":00";
            }

        }

    } else if (schedule.type == 'weekly') {

        text += "Weekly";

        $('#weekly').prop('checked', true);

        $('#weekly_form').show();

        onChangeWeeklyForm('weekly_at_val');

        if (schedule.week_days.length > 0) {

            text += " on ";

            for (index in schedule.week_days) {

                day = schedule.week_days[index];

                text += week_days[day] + ",";

                $('#' + day).prop('checked', true);
            }
        }

        text = text.slice(0, -1);

        select_at_val(schedule.at, 'weekly_at_val');

        if (schedule.at < 10) {

            text += " at 0" + schedule.at + ":00";

        } else {

            text += " at " + schedule.at + ":00";
        }

    } else if (schedule.type == 'monthly') {

        text += "Monthly";

        $('#monthly').prop('checked', true);

        $('#monthly_form').show();

        onChangeMonthlyForm('monthly_at_val');

        select_at_val(schedule.at, 'monthly_at_val');

        if (schedule.first_week_day > -1) {

            $('#first_day_of_month').prop('disabled', false);

            $('#monthly_first').prop('checked', true);

            $('#first_day_of_month').val(schedule.first_week_day);

            text += " on first " + schedule.first_week_day;

        } else {

            $('#monthly_days').prop('disabled', false);

            $('#monthly_on_days_check').prop('checked', true);

            days = "";

            for (index in schedule.days) {

                days += schedule.days[index] + ",";

            }

            $('#monthly_days').val(days.slice(0, -1));
            text += " on " + days.slice(0, -1);
        }

        if (schedule.at < 10) {
            text += " at 0" + schedule.at + ":00";
        } else {
            text += " at " + schedule.at + ":00";
        }
    }

    $('#selected_schedule').html(text);
    return text;
}


function enabelAndDisableAtVals(name, value, target_id){
    if ($('input[name='+name+']:checked').val() == value){
        $('#' + target_id).prop('disabled', false);
        $('#daily_every_val_hour').prop('disabled', true);
        $('#daily_every_val_minute').prop('disabled', true);
        $('#daily_every_type').prop('disabled', true);
    }
}


function enabelAndDisableVals(name,value,target_id1 , target_id2 , target_id3){
    if ($('input[name='+name+']:checked').val() == value){
        $('#' + target_id1).prop('disabled', false);
        $('#' + target_id2).prop('disabled', false);
        $('#' + target_id3).prop('disabled', false);
        $('#daily_at_val').prop('disabled', true);
    }
}


function enabelAndDisableVal(name , value, target_id, target_id2){
    if ($('input[name='+name+']:checked').val() == value){
        $('#' + target_id).prop('disabled', false);
        $('#' + target_id2).prop('disabled', true);
    }else{
        $('#' + target_id).prop('disabled', true);
        $('#' + target_id2).prop('disabled', false);
    }
}



function select_at_val(at, id) {
    if (at > -1) {
        at_val = "";
        if (at < 10) {
            at_val = "0";
        }
        at_val += String(at);
        $('#' + id).val(at_val);
    }
}


function onChangeDailyForm(id) {
    appendTimeAt(id);
    $('#monthly_form').hide();
    $('#weekly_form').hide();
    $('#daily_form').show();
}


function onChangeWeeklyForm(id) {
    appendTimeAt(id);
    $('#monthly_form').hide();
    $('#weekly_form').show();
    $('#daily_form').hide();
}


function onChangeMonthlyForm(id) {
    appendTimeAt(id);
    $('#monthly_form').show();
    $('#weekly_form').hide();
    $('#daily_form').hide();
}


function onChangeDailyEveryType() {
    if ($('#daily_every_type').val() == 'minutes') {
        $('#daily_every_val_hour').hide();
        $('#daily_every_val_minute').show();
    } else {
        $('#daily_every_val_hour').show();
        $('#daily_every_val_minute').hide();
    }
}


function appendTimeAt(id) {
    for (var i = 0; i < 24; i++) {
        if (i < 10) {
            $('#' + id).append("<option value='0" + i + "'>0" + i + ":00</option>");
        } else {
            $('#' + id).append("<option value='" + i + "'>" + i + ":00</option>");
        }
    }
}


function schedule_types(types) {

    if ($('input[name=schedule_type]:checked').val() == "daily") {

        $('#daily_form').show();
    } else if ($('input[name=schedule_type]:checked').val() == "weekly") {
        $('#weekly_form').show();
    } else if ($('input[name=schedule_type]:checked').val() == "monthly") {
        $('#monthly_form').show();
    } else {
        $('#monthly_form').hide();
        $('#weekly_form').hide();
        $('#daily_form').hide();
    }

    //$('input[type=checkbox]').removeAttr('checked');
    //$('input[type=radio]').prop('checked', false);

    //$('#daily_form').hide();
    //$('#weekly_form').hide();
    //$('#monthly_form').hide();

    if ($.inArray('daily', types) == -1) {
        $('#daily_radio').hide();

    } else {
        $('#daily_radio').show();
    }
    if ($.inArray('weekly', types) == -1) {
        $('#weekly_radio').hide();

    } else {
        $('#weekly_radio').show();
    }
    if ($.inArray('monthly', types) == -1) {
        $('#monthly_radio').hide();

    } else {
        $('#monthly_radio').show();
    }

}
var selected_schedule = [];

function submitSchedule(event) {
    $('#submit_schedule_btn').removeAttr("data-dismiss");

    var week_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    selected_schedule = [];

    var schedule = {"type": "", "every": -1, "unit": "", "at": -1, "week_days": [], "days": [], "first_week_day": -1};

    var errors = [];

    if ($('input[name=schedule_type]:checked').val() == "daily") {

        schedule.type = "daily";

        selected_schedule.push("Daily");

        if ($('input[name=daily_type]:checked').val() == "daily_at") {

            if ($('#daily_at_val').val() == 'none') {

                errors.push(messages_schedule.schedule_error_at_time_field);

            } else {

                selected_schedule.push("at " + $('#daily_at_val').val() + ":00");

                schedule.at = parseInt($('#daily_at_val').val());

            }

        } else if ($('input[name=daily_type]:checked').val() == "daily_every") {

            if ($('#daily_every_type').val() == 'hours') {

                if ($('#daily_every_val_hour').val() == 'none') {

                    errors.push(messages_schedule.schedule_error_every_field);

                } else {
                    //
                    if(parseInt($('#daily_every_val_hour').val()) == 1){
                        selected_schedule.push("every " + $('#daily_every_val_hour').val() + " Hour");
                    }else{
                        selected_schedule.push("every " + $('#daily_every_val_hour').val() + " Hours");
                    }

                    schedule.every = parseInt($('#daily_every_val_hour').val());
                }

            } else if ($('#daily_every_type').val() == 'minutes') {

                if ($('#daily_every_val_minute').val() == 'none') {

                    errors.push(messages_schedule.schedule_error_every_field);

                } else {
                    selected_schedule.push("every " + $('#daily_every_val_minute').val() + " Minutes");

                    schedule.every = parseInt($('#daily_every_val_minute').val());
                }

            }
            schedule.unit = $('#daily_every_type').val();

        } else {

            errors.push(messages_schedule.schedule_error_frequently_daily_type);
        }

    } else if ($('input[name=schedule_type]:checked').val() == "weekly") {

        schedule.type = "weekly";

        var days = "on ";

        selected_schedule.push("Weekly");

        $('input[type=checkbox]').each(function () {

            if (this.checked) {
                day_of_week = $(this).val();

                days += week_days[day_of_week] + " ,";
                schedule.week_days.push(day_of_week);

            }
        });

        if (schedule.week_days.length < 1) {

            errors.push(messages_schedule.schedule_error_frequently_week_days);

        } else {

            selected_schedule.push(days.slice(0, -1));
        }


        if ($('#weekly_at_val').val() == "none") {
            errors.push(messages_schedule.schedule_error_at_time_field);

        } else {

            selected_schedule.push("at " + $('#weekly_at_val').val() + ":00");
            schedule.at = parseInt($('#weekly_at_val').val());
        }

    } else if ($('input[name=schedule_type]:checked').val() == "monthly") {

        schedule.type = "monthly";

        selected_schedule.push("Monthly");

        if ($('input[name=monthly_days_check]:checked').val() == "monthly_on_days_check") {

            var error_count = 0;

            var on_days = "on ";

            if ($('#monthly_days').val() != "" && $('#monthly_days').val().indexOf(',') > -1) {

                monthly_days = $('#monthly_days').val().split(",");

                for (day in monthly_days) {

                    day_number = parseInt(monthly_days[day]);

                    if (!$.isNumeric(day_number)) {

                        error_count++;

                    } else {

                        schedule.days.push(day_number);
                        on_days += day_number + " ,";
                    }
                }

                selected_schedule.push(on_days.slice(0, -1));

            } else if($.isNumeric($('#monthly_days').val())){
                num = parseInt($('#monthly_days').val());
                if(num > 31 || num < 1){
                    error_count++;

                }else{
                    schedule.days.push(num);
                    on_days += num + " ,";
                    selected_schedule.push(on_days.slice(0, -1));
                }

            } else {
                error_count++;
            }

            if (error_count > 0) {

                errors.push(messages_schedule.schedule_error_frequently_month_days);

            }
        } else if ($('input[name=monthly_days_check]:checked').val() == "monthly_first") {

            if ($('#first_day_of_month').val() == 'none') {

                errors.push(messages_schedule.schedule_error_frequently_first_day_of_month);

            } else {

                schedule.first_week_day = parseInt($('#first_day_of_month').val());

                selected_schedule.push("on first " + week_days[$('#first_day_of_month').val()]);
            }

        } else {

            errors.push(messages_schedule.schedule_error_frequently_month_type);

        }

        if ($('#monthly_at_val').val() == "none") {
            errors.push(messages_schedule.schedule_error_at_time_field);

        } else {

            schedule.at = parseInt($('#monthly_at_val').val());
            selected_schedule.push("at " + $('#monthly_at_val').val() + ":00");
        }

    } else {
        errors.push(messages_schedule.schedule_error_frequently_type);

    }

    if (errors.length > 0) {
        alert(messages_schedule.schedule_error_msgs + "\n" + errors.join("\n"));
        //console.log(errors)

    } else {
        var myJSON = JSON.stringify(schedule);
        var selected_schedule_str = "";
        for (i in selected_schedule) {
            selected_schedule_str += selected_schedule[i] + " ";
        }
        $('#schedule_object').val(myJSON);

        $('#selected_schedule').val(selected_schedule_str);
        console.log(schedule.type);
        $('#submit_schedule_btn').attr('data-dismiss', 'modal');
    }

    console.log(selected_schedule_str);

//console.log("schedule "+myJSON);
//console.log("schedule 2 "+$('#schedule_object').val());

}


function cancelSchedule() {

    if (selected_schedule.length < 1 && global_schedule.length < 1) {
        $('input[type=checkbox]').removeAttr('checked');
        $('input[type=radio]').prop('checked', false);
    }
}


