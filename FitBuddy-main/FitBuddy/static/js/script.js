/**
 * FitBuddy Interactive Browser Logic
 */

// Global helper function for feedback suggestion chips
function applySuggestion(text) {
  var feedbackInput = document.getElementById("feedbackInput");
  if (feedbackInput) {
    feedbackInput.value = text;
    feedbackInput.focus();
    feedbackInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

(function () {
  'use strict';

  // 1. Intensity Pills Selection Handler
  document.querySelectorAll(".pill").forEach(function (pill) {
    pill.addEventListener("click", function () {
      document.querySelectorAll(".pill").forEach(function (item) {
        item.classList.remove("selected");
      });
      pill.classList.add("selected");
      var radioInput = pill.querySelector("input");
      if (radioInput) {
        radioInput.checked = true;
      }
    });
  });

  // 2. Generate Plan Form Loading Handler
  var generateForm = document.getElementById("genForm");
  if (generateForm) {
    generateForm.addEventListener("submit", function (event) {
      var username = generateForm.username ? generateForm.username.value.trim() : "";
      var userId = generateForm.user_id ? generateForm.user_id.value.trim() : "";
      var age = generateForm.age ? generateForm.age.value : "";
      var weight = generateForm.weight ? generateForm.weight.value : "";
      var goal = generateForm.goal ? generateForm.goal.value : "";
      var expLevel = generateForm.experience_level ? generateForm.experience_level.value : "";
      var intensityRadio = document.querySelector('input[name="intensity"]:checked');

      if (!username || !userId || !age || !weight || !goal || !expLevel || !intensityRadio) {
        event.preventDefault();
        alert("Please fill in all required fields, including experience level and training intensity.");
        return;
      }

      var btnLabel = document.getElementById("btnLabel");
      var btnSpinner = document.getElementById("btnSpinner");
      var submitBtn = document.getElementById("submitBtn");

      if (btnLabel) btnLabel.textContent = "Architecting Plan…";
      if (btnSpinner) btnSpinner.classList.add("visible");
      if (submitBtn) submitBtn.disabled = true;
    });
  }

  // 3. Feedback Refinement Form Loading Handler
  var feedbackForm = document.getElementById("feedbackForm");
  if (feedbackForm) {
    feedbackForm.addEventListener("submit", function () {
      var refineBtnLabel = document.getElementById("refineBtnLabel");
      var refineSpinner = document.getElementById("refineSpinner");
      var refineBtn = document.getElementById("refineBtn");

      if (refineBtnLabel) refineBtnLabel.textContent = "Refining Plan…";
      if (refineSpinner) refineSpinner.classList.add("visible");
      if (refineBtn) refineBtn.disabled = true;
    });
  }

})();
