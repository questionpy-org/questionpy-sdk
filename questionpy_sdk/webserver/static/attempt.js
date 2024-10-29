/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

/**
 * Unescape and replace HTML entities.
 *
 * @param {string} input
 * @returns {string}
 */
function htmlDecode(input) {
  var txt = document.createElement("textarea");
  txt.innerHTML = input;
  return txt.value;
}

class Attempt {
    #formulation;
    #generalFeedback;
    #specificFeedback;
    #rightAnswer;

    /**
     * @param {Element} formulationElement
     * @param {Element} generalFeedbackElement
     * @param {Element} specificFeedbackElement
     * @param {Element} rightAnswer
     */
    constructor(formulationElement, generalFeedbackElement, specificFeedbackElement, rightAnswer) {
        this.#formulation = formulationElement;
        this.#generalFeedback = generalFeedbackElement;
        this.#specificFeedback = specificFeedbackElement;
        this.#rightAnswer = rightAnswer;
    }

    /**
     * Get the top html element where the question's formulation xhtml was inserted.
     *
     * @returns {Element}
     */
    get formulationElement() {
        return this.#formulation;
    }

    /**
     * Get the top html element where the question's general feedback xhtml was inserted.
     *
     * @returns {Element}
     */
    get generalFeedbackElement() {
        return this.#generalFeedback;
    }

    /**
     * Get the top html element where the question's specific feedback xhtml was inserted.
     *
     * @returns {Element}
     */
    get specificFeedbackElement() {
        return this.#specificFeedback;
    }

    /**
     * Get the top html element where the question's right answer xhtml was inserted.
     *
     * @returns {Element}
     */
    get rightAnswerElement() {
        return this.#rightAnswer;
    }

    /**
     * Get an element by the id that was given in the question's xhtml.
     *
     * @param {string} id
     * @return {?Element}
     */
    getElementById(id) {
        return document.getElementById(id);
    }

    /**
     * Get an element by the name that was given in the question's xhtml.
     *
     * @param {string} name
     * @return {NodeListOf<Element>}
     */
    getElementsByName(name) {
        return document.getElementsByName(name);
    }
}
