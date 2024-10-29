define(function () {
    return {
        initButton: function (attempt) {
            attempt.getElementById("mybutton").addEventListener("click", function (event) {
                event.target.disabled = true;
                attempt.getElementById("hiddenInput").value = "secret";
            })
        },
        hello: function (attempt, param) {
            console.log("hello " + param);
        },
    }
});
