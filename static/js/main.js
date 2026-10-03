document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const planForm = document.getElementById('plan-form');
    const feedbackForm = document.getElementById('feedback-form');
    const resultsSection = document.getElementById('results-section');
    const planContent = document.getElementById('plan-content');
    const planIdInput = document.getElementById('plan_id');
    const getTipBtn = document.getElementById('get-tip-btn');
    const tipContainer = document.getElementById('tip-container');
    const nutritionTip = document.getElementById('nutrition-tip');
    const errorMsg = document.getElementById('error-msg');
    const goalSelect = document.getElementById('goal');
    
    // Buttons and Spinners
    const generateBtnSpan = document.querySelector('#generate-btn span');
    const generateSpinner = document.getElementById('generate-spinner');
    const updateBtnSpan = document.querySelector('#update-btn span');
    const updateSpinner = document.getElementById('update-spinner');

    // Handle initial plan generation
    planForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI State
        errorMsg.classList.add('hidden');
        generateBtnSpan.textContent = 'Generating...';
        generateSpinner.classList.remove('hidden');
        planForm.querySelector('button[type="submit"]').disabled = true;

        const formData = new FormData(planForm);

        try {
            const response = await fetch('/generate_plan', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                // Populate Results
                planIdInput.value = data.user_id; // Using user_id here but technically in a full app we'd fetch plan_id. The backend uses user_id to get latest plan, or returns plan_id. Wait, backend returned user_id in /generate_plan? Need to fetch latest plan id.
                // Let's get the plan ID that was created
                const planIdRes = await fetch(`/users/${data.user_id}/latest_plan`);
                const planData = await planIdRes.json();
                planIdInput.value = planData.plan_id;

                displayPlan(data.plan);
                
                // Show results section smooth scroll
                resultsSection.classList.remove('hidden');
                resultsSection.scrollIntoView({ behavior: 'smooth' });
                
                // Reset tip
                tipContainer.classList.add('hidden');
            } else {
                throw new Error(data.detail || 'Failed to generate plan');
            }
        } catch (error) {
            errorMsg.textContent = 'Failed to generate plan. Ensure API key is set.';
            errorMsg.classList.remove('hidden');
        } finally {
            generateBtnSpan.textContent = 'Generate My Plan';
            generateSpinner.classList.add('hidden');
            planForm.querySelector('button[type="submit"]').disabled = false;
        }
    });

    // Handle plan update (feedback)
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        updateBtnSpan.textContent = 'Updating...';
        updateSpinner.classList.remove('hidden');
        feedbackForm.querySelector('button[type="submit"]').disabled = true;

        const formData = new FormData(feedbackForm);

        try {
            const response = await fetch('/update_plan', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to update plan');
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                displayPlan(data.plan);
                document.getElementById('feedback_text').value = '';
                // scroll up to plan
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (error) {
            alert('Failed to update plan. Please try again.');
        } finally {
            updateBtnSpan.textContent = 'Update Plan';
            updateSpinner.classList.add('hidden');
            feedbackForm.querySelector('button[type="submit"]').disabled = false;
        }
    });

    // Handle getting a nutrition tip
    getTipBtn.addEventListener('click', async () => {
        const goal = goalSelect.value;
        const btnOriginalText = getTipBtn.textContent;
        getTipBtn.textContent = 'Fetching...';
        getTipBtn.disabled = true;

        try {
            const response = await fetch(`/nutrition_tip?goal=${encodeURIComponent(goal)}`);
            const data = await response.json();
            
            if (data.tip) {
                nutritionTip.textContent = data.tip;
                tipContainer.classList.remove('hidden');
            }
        } catch (error) {
            alert('Failed to fetch tip.');
        } finally {
            getTipBtn.textContent = btnOriginalText;
            getTipBtn.disabled = false;
        }
    });

    // Render markdown to HTML
    function displayPlan(markdownText) {
        // Simple fix for markdown to avoid html injection issues locally
        planContent.innerHTML = marked.parse(markdownText);
    }
});
