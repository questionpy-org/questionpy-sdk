

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
 * @param from_reference the absolute reference (list) of the current element
 * @param to_reference  the relative reference (list) to the target element
 * @return list
 */
export function merge_references(from_reference, to_reference) {
    console.log('from: ', from_reference)
    console.log('to: ', to_reference)
    from_reference = Array.from(from_reference)
    for (var i = 0; i <= to_reference.filter(ref => ref == '..').length; i++) {
        from_reference.pop();
    }
    return from_reference.concat(to_reference);
}


export function change_reference_trunk(reference, new_trunc) {
    for (let i = 0; i < new_trunc.length; i++) {
        reference[i] = new_trunc[i];
    }
    return reference;
}
