/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import * as conditions from "./conditions.js";

/**
 * Selects all elements that have a list of conditions as a data attribute. The lists of conditions are an
 * unparsed JSON string and represent either a hide_if list or a disable_if list (see: {@link conditions.Types}).
 *
 *
 * @returns {[Element]} list of elements
 */
function get_elements_with_conditions() {
    let elements_with_conditions = []
    for (const value in conditions.Types.values) {
        const condition_type = new conditions.Types(value);
        document.querySelectorAll(condition_type.to_selector())
            .forEach(element => {
                add_conditions_to_element(element, condition_type)
                elements_with_conditions.push(element);
            });
    }
    return elements_with_conditions;
}


/**
 * Parses the condition list from the data attribute of the element into a list of {@link conditions}.
 *
 * @param {HTMLElement} element a form element
 * @param {object} element.conditions object containing the list of conditions
 * @param {conditions.Types} condition_type the type of the condition list
 * @param {string} condition_type.value from ['disable_if', 'hide_if']
 * @return void
 */
function add_conditions_to_element(element, condition_type) {
    if (!element.conditions) {
        element.conditions = {};
    }
    element.conditions[condition_type.value] = [];
    JSON.parse(element.dataset[condition_type.value]).forEach(object => {
        var reference = JSON.parse(element.dataset['absolute_path'])
        let condition = conditions.Condition.from_object(object, reference);
        condition.targets.forEach(target => add_source_element_to_target(target, element, condition_type));
        element.conditions[condition_type.value].push(condition);
    });
}


/**
 * Adds the source element to the targets list of source elements.
 * Adds the event listener corresponding to the condition_type to the target.
 * When the target's event listener is triggered, the source list contains all the elements whose conditions have to be
 * checked.
 *
 * @param {HTMLElement} target the conditions target
 * @param {Element} source element with the condition
 * @param {conditions.Types} condition_type
 * @param {string} condition_type.value from ['disable_if', 'hide_if']
 */
function add_source_element_to_target(target, source, condition_type) {
    if (!target.source_elements) {
        target.source_elements = []
    }
    target.source_elements.push(source);
    switch (condition_type.value) {
        case conditions.Types.values.hide_if:
            target.addEventListener("change", hide_if_listener);
            break;
        case conditions.Types.values.disable_if:
            target.addEventListener("change", disable_if_listener);
            break;
    }
}


/**
 * Calls toggle_visibility on the source element.
 *
 * @see toggle_visibility
 * @param {Event} event
 */
function hide_if_listener(event) {
    event.currentTarget.source_elements.forEach(element => toggle_visibility(element));
}


/**
 * Calls toggle_visibility on the source element.
 *
 * @see toggle_availability
 * @param {Event} event
 */
function disable_if_listener(event) {
    event.currentTarget.source_elements.forEach(element => toggle_availability(element));
}


/**
 * If every condition in hide_if is true, changes the display style to 'none'. Else to 'inherit'.
 *
 * @param {Element} element
 * @param {object} element.conditions object containing the list of conditions
 * @param {object} element.style
 */
function toggle_visibility(element) {
    if (element.conditions[conditions.Types.values.hide_if].every(condition => condition.is_true())) {
        element.style.display = "none";
    } else {
        element.style.display = "inherit";
    }
}


/**
 * If every condition in disable_if is true, recursively disables the element and its children.
 * Else recursively enables the element and its children.
 *
 * @param {Element} element
 * @param {object} element.conditions object containing the list of conditions
 */
function toggle_availability(element) {
    if (element.conditions[conditions.Types.values.disable_if].every(condition => condition.is_true())) {
        disable(element);
    } else {
        enable(element);
    }
}


/**
 * Disable the element and its children recursively.
 *
 * @param {Element} element
 */
function disable(element) {
    element.disabled = true;
    Array.from(element.children).forEach(child => disable(child))
}


/**
 * Enable the element and its children recursively.
 *
 * @param {Element} element
 */
function enable(element) {
    element.disabled = false;
    Array.from(element.children).forEach(child => enable(child))
}


/**
 * Calls the toggle method corresponding to the condition type.
 *
 * @param {Element} element
 * @param {string} condition_type_value
 */
function toggle_condition(element, condition_type_value) {
    switch (condition_type_value) {
        case conditions.Types.values.hide_if:
            toggle_visibility(element);
            break;
        case conditions.Types.values.disable_if:
            toggle_availability(element);
            break;
    }
}


/**
 * Iterates over a list of elements, containing conditions and checks the conditions.
 *
 * @param {[Element]} elements list of form elements
 */
function check_all_element_conditions(elements) {
    for (const value in conditions.Types.values) {
        Array.from(elements)
            .filter(element => !(element.conditions[value] === undefined || element.conditions[value].length === 0))
            .forEach(element => toggle_condition(element, value));
    }
}


/**
 * Creates JSON object from element in a form.
 * @param form
 * @return {}
 */
function create_json_form_data(form) {
    const json_form_data = {};
    for (const pair of new FormData(form)) {
        if (json_form_data[pair[0]]) {
            json_form_data[pair[0]].push(pair[1]);
        } else if (pair[0].endsWith('_[]')) {
            json_form_data[pair[0]] = [pair[1]];
        } else {
            json_form_data[pair[0]] = pair[1];
        }
    }

    for (var entry in json_form_data) {
        if (entry.endsWith('_[]')) {
            json_form_data[entry.substring(0, entry.length - 3)] = json_form_data[entry];
            delete json_form_data[entry];
        }
    }

    return json_form_data;
}


/**
 *
 * @param url
 * @param headers
 * @param body
 * @return {Promise<*>}
 */
async function post_http_request(url, headers, body) {
    if (!url || !headers || !body) {
        throw new Error("One or more POST request parameters was not passed.");
    }
    try {
        return await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(body)
        });
    } catch (err) {
        console.error(`Error at fetch POST: ${err}`);
        throw err;
    }
}


/**
 * Event handler for the "submit" event of the form.
 *
 * @param event
 */
async function handle_submit(event) {
    // prevent reload on submit
    event.preventDefault();

    const route = event.target.getAttribute('data-route');
    const successAction = event.target.getAttribute('data-success-action')
    const json_form_data = create_json_form_data(event.target);
    const headers = {'Content-Type': 'application/json'}
    const response = await post_http_request(route, headers, json_form_data);
    if (response.status >= 200 && response.status < 300) {
        if (successAction === "success-info") {
            document.getElementById('submit_success_info').hidden = false;
        } else if (successAction === "reload") {
            window.location.reload();
        }
    } else {
        alert('An error occured.');
    }
}


/**
 * Adds a repetition element to the repetition element parent.
 *
 * Adds n repetitions, where n = repetition_increment, to the parent element.
 * @param event
 */
async function add_repetition_element(event) {
    // prevent reload on submit
    event.preventDefault();
    const form = document.getElementById('options_form');

    const data = {
        'form_data': create_json_form_data(form),
        'element-name': event.target.name,
        'increment': event.target.dataset['repetition_increment']
    }

    const headers = {'Content-Type': 'application/json'}
    const response = await post_http_request('/repeat', headers, data);
    if (response.status == 200) {
        document.getElementById('submit_success_info').hidden = null;
        window.location.reload();
    } else {
        alert('An error occured.');
    }
}


/**
 * When a Delete Button is clicked, removes the corresponding repetition.
 */
function delete_repetition_element(event) {
    // prevent reload on click
    event.preventDefault();
    // count current repetitions - 1 for the add-repetition button
    const current_repetitions = event.target.parentElement.parentElement.children.length - 1;
    if (current_repetitions > event.target.dataset['initial_repetitions']) {
        event.target.parentElement.remove();
    }
}


/**
 * Hides all help_dialogs when the target of the event is not the previously clicked element.
 * @param event
 * @return {Promise<void>}
 */
function hide_help_dialogs(event) {
    const help_dialogs = document.getElementsByClassName("help_dialog");

    if (event.target !== help_icon) {
        Array.from(help_dialogs).forEach(dialog => dialog.style.display = "none");
    }
}


/**
 * Shows the corresponding help dialog when a help icon is clicked.
 * @param event click
 * @return {Promise<void>}
 */
function show_help_dialog(event) {
    hide_help_dialogs(event);

    const icon = event.target;
    help_icon = icon;

    const help_dialog = icon.parentElement.getElementsByClassName("help_dialog")[0];
    help_dialog.style.left = `${icon.offsetLeft}px`;
    help_dialog.style.display = 'block';
}


/**
 * Current selected help_icon.
 * @type {HTMLElement}
 */
let help_icon = null;

document.addEventListener("DOMContentLoaded", function () {
    const elements = get_elements_with_conditions();
    // check conditions manually. without the change event
    check_all_element_conditions(elements);

    const forms = document.querySelectorAll('form');
    Array.from(forms).forEach(form => form.addEventListener('submit', handle_submit));

    const repetition_buttons = document.getElementsByClassName("repetition-button");
    Array.from(repetition_buttons).forEach(button => button.addEventListener("click", add_repetition_element));

    const repetition_buttons_delete = document.getElementsByClassName("repetition-button-delete");
    Array.from(repetition_buttons_delete).forEach(button => button.addEventListener("click", delete_repetition_element));

    const help_icons = document.getElementsByClassName("help_icon");
    Array.from(help_icons).forEach(icon => icon.addEventListener("click", show_help_dialog));

    document.addEventListener('click', hide_help_dialogs);
})
