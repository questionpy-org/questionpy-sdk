export class Types {
    constructor(value) {
        this.value = value
    }

    static values = {
        hide_if: 'hide_if',
        disable_if: 'disable_if'
    }

    /**
     * Format the condition type to a CSS selector.
     * @example "[data-disable_if]" for condition_type "disable_if"
     * @return {string}
     */
    to_selector() {
        return "[data-".concat(this.value, "]");
    }
}

/**
 * Conditions are used to decide wether to hide or disable an element or a group of elements
 * depending on the state of other form elements.
 */
export class Condition {
    constructor(kind, name) {
        if (this.constructor === Condition) {
            throw new Error("Cannot create instance of abstract class")
        }
        this.kind = kind;
        this.name = name;
        this.targets = Array.from(document.getElementsByName(this.name));
    }

    /**
     * Create a Condition from a plain javascript object. The Condition type is chosen according to the
     * object kind.
     *
     * Ex.: object.kind = "is_checked" returns new IsChecked(object.name)
     * @param object the plain javascript object
     * @returns {Condition} the condition object
     */
    static from_object(object) {
        if (!object || !object.kind) {
            throw new Error("Invalid condition")
        }
        switch (object.kind) {
            case "is_checked":
                return new IsChecked(object.name);
            case "is_not_checked":
                return new IsNotChecked(object.name);
            case "equals":
                return new Equals(object.name, object.value);
            case "does_not_equal":
                return new DoesNotEqual(object.name, object.value);
            case "in":
                return new In(object.name, object.value);
            default:
                throw new Error("Invalid condition kind")
        }
    }

    /**
     * Check if the condition is true.
     * @return {boolean}
     */
    is_true() {
        throw new Error("not implemented");
    };
}

export class IsChecked extends Condition {
    constructor(name) {
        super("is_checked", name);
    }

    is_true() {
        return this.targets.every(target => target.checked);
    }
}


export class IsNotChecked extends Condition {
    constructor(name) {
        super("is_not_checked", name);
    }

    is_true() {
        return this.targets.every(target => !target.checked);
    }
}


export class Equals extends Condition {
    constructor(name, value) {
        super("equals", name);
        this.value = value;
    }

    is_true() {
        return this.targets.every(target => target.value === this.value);
    }
}


export class DoesNotEqual extends Condition {
    constructor(name, value) {
        super("does_not_equal", name);
        this.value = value;
    }

    is_true() {
        return this.targets.every(target => target.value !== this.value);
    }
}


export class In extends Condition {
    constructor(name, value) {
        super("in", name);
        this.value = value;
    }

    is_true() {
        return this.targets.every(target => this.value.includes(target.value));
    }
}
