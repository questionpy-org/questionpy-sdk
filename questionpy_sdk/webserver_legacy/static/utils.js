

export function to_reference_string(reference) {
    return reference.join('][').replace(']', '').concat(']');
}


/**
 *
 * @param reference_string
 * @return list
 */
export function to_reference(reference_string) {
    reference_string.replaceAll(']', '');
    return reference_string.split('[');
}


/**
 * Resolve the absolute reference of the target element.
 *
 * e.g. merge_reference(["sect", "my_input"], ["chk"]) ->  ["sect", "chk"]
 * see: https://github.com/questionpy-org/moodle-qtype_questionpy/blob/dev/classes/form/context/render_context.php#L172-L201
 * @param from_reference the absolute reference (list) of the current element
 * @param to_reference  the relative reference (list) to the target element
 * @return list
 */
export function merge_references(from_reference, to_reference) {
    from_reference = Array.from(from_reference);
    from_reference.pop();
    to_reference.forEach(part => {
        if (part === '..') {
            const removed = from_reference.pop();
            if (typeof removed == 'number') {
                from_reference.pop()
            }
        } else {
            from_reference.push(part);
        }
    });
    return from_reference;
}
