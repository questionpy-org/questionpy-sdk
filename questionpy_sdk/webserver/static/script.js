import * as conditions from "./conditions.js";


/**
 * Selects all elements which have a list of conditions as a data attribute. The lists of conditions are an
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
 * @param {Element} element a form element
 * @param {object} element.conditions object containing the list of conditions
 * @param {conditions.Types} condition_type the type of the condition list
 * @param {string} condition_type.value from ['disable_if', 'hide_if']
 * @return void
 */
function add_conditions_to_element(element, condition_type){
    if (!element.conditions) {
        element.conditions = {};
    }
    element.conditions[condition_type.value] = [];
    JSON.parse(element.getAttribute("data-"+condition_type.value)).forEach(object => {
        let condition = conditions.Condition.from_object(object);
        add_source_element_to_target(condition.target, element, condition_type);
        element.conditions[condition_type.value].push(condition);
    });
}


/**
 * Adds the source element to the targets list of source elements.
 * Adds the event listener corresponding to the condition_type to the target.
 * When the targets event listener is triggered, the source list contains all the elements which conditions have to be
 * checked.
 *
 * @param {HTMLElement} target the conditions target
 * @param {Element} source element with the condition
 * @param {conditions.Types} condition_type
 * @param {string} condition_type.value from ['disable_if', 'hide_if']
 */
function add_source_element_to_target(target, source, condition_type) {
    if (!target['source_elements']) {
        target['source_elements'] = []
    }
    target['source_elements'].push(source);
    switch(condition_type.value) {
        case conditions.Types.values.hide_if:
            target.addEventListener("change", hide_if_listener); break;
        case conditions.Types.values.disable_if:
            target.addEventListener("change", disable_if_listener); break;
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
    switch(condition_type_value) {
        case conditions.Types.values.hide_if:
            toggle_visibility(element); break;
        case conditions.Types.values.disable_if:
            toggle_availability(element); break;
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
            .filter(element => !(element['conditions'][value] === undefined || element['conditions'][value].length === 0))
            .forEach(element => toggle_condition(element, value));
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const elements = get_elements_with_conditions();
    // check conditions manually. without the change event
    check_all_element_conditions(elements);
})