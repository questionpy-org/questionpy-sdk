import { returnTest2 } from './test2.js';

export function initButton(attempt, [buttonId, inputId, secretValue]) {
    console.log("called initButton");

    if (returnTest2() !== "test2") {
        console.error("method did not return 'test2'");
    }

    document.getElementById(buttonId).addEventListener("click", function (event) {
        event.target.disabled = true;
        document.getElementById(inputId).value = secretValue;
    })
}

export function hello(attempt, param) {
    console.log("hello " + param);
}
