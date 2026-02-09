document.addEventListener('DOMContentLoaded', () => {
    const processBtn = document.getElementById('processBtn');
    const clearBtn = document.getElementById('clearBtn');
    const loadSampleBtn = document.getElementById('loadSampleBtn');
    const claimInput = document.getElementById('claimInput');
    const resultArea = document.getElementById('resultArea');

    const elements = {
        route: document.getElementById('recommendRoute'),
        reasoning: document.getElementById('reasoningText'),
        alertContainer: document.getElementById('alertContainer'),
        missingSection: document.getElementById('missingFieldsSection'),
        missingList: document.getElementById('missingFieldsList'),
        inconsistentSection: document.getElementById('inconsistentSection'),
        inconsistentList: document.getElementById('inconsistentList'),

        policy: document.getElementById('val_policy'),
        holder: document.getElementById('val_holder'),
        dates: document.getElementById('val_dates'),
        loss_dt: document.getElementById('val_loss_dt'),
        location: document.getElementById('val_loss_loc'),
        type: document.getElementById('val_type'),
        claimant: document.getElementById('val_claimant'),
        third: document.getElementById('val_third'),
        contact: document.getElementById('val_contact'),
        vin: document.getElementById('val_vin'),
        estimate: document.getElementById('val_estimate'),
        initial: document.getElementById('val_initial_est'),
        desc: document.getElementById('val_desc')
    };

    const SAMPLE_ACORD = `ACORD 80 AUTOMOBILE LOSS NOTICE
AGENCY: Standard Insurance
POLICY NUMBER: POL-992341
NAME OF INSURED: Johnathan Doe
INSURED'S MAILING ADDRESS: 123 Maple Street, Springfield
PRIMARY PHONE #: (555) 0199
PRIMARY E-MAIL ADDRESS: j.doe@email.com

LOSS DETAILS
DATE OF LOSS AND TIME: 02/05/2026 02:30 PM
LOCATION OF LOSS: Intersection of 5th and Baker
POLICE DEPARTMENT CONTACTED: Springfield PD
REPORT NUMBER: SPD-8877

DESCRIPTION OF ACCIDENT: 
The driver was moving forward and collided with a stationary fence while attempting to park.

VEHICLE INFORMATION
YEAR: 2022
MAKE: Toyota
MODEL: Camry
V.I.N.: VIN1234567890
PLATE NUMBER: ABC-1234
DESCRIBE DAMAGE: Front bumper and grille damage.
ESTIMATE AMOUNT: 1,200.00
CLAIM TYPE: Collision
INITIAL ESTIMATE: 1,200.00`;

    loadSampleBtn.addEventListener('click', () => {
        claimInput.value = SAMPLE_ACORD;
    });

    processBtn.addEventListener('click', async () => {
        const content = claimInput.value.trim();
        if (!content) return;

        processBtn.classList.add('loading');

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error(error);
        } finally {
            processBtn.classList.remove('loading');
        }
    });

    clearBtn.addEventListener('click', () => {
        claimInput.value = '';
        resultArea.classList.add('hidden');
    });

    function displayResults(data) {
        window.currentAnalysis = data;
        resultArea.classList.remove('hidden');
        resultArea.scrollIntoView({ behavior: 'smooth' });

        const f = data.extractedFields;

        elements.route.innerText = data.recommendedRoute;
        elements.reasoning.innerText = data.reasoning;
        elements.route.style.color = getRouteColor(data.recommendedRoute);

        // Alerts
        const hasMissing = data.missingFields.length > 0;
        const hasInconsistent = data.inconsistentFields.length > 0;

        elements.alertContainer.classList.toggle('hidden', !hasMissing && !hasInconsistent);
        elements.missingSection.classList.toggle('hidden', !hasMissing);
        elements.inconsistentSection.classList.toggle('hidden', !hasInconsistent);

        if (hasMissing) {
            elements.missingList.innerHTML = data.missingFields.map(f => `<span>${f}</span>`).join('');
        }
        if (hasInconsistent) {
            elements.inconsistentList.innerHTML = data.inconsistentFields.map(f => `<span>${f}</span>`).join('');
        }

        // Mapping Data
        elements.policy.innerText = f.policy.policy_number || 'Missing';
        elements.holder.innerText = f.policy.policyholder_name || 'Missing';
        elements.dates.innerText = f.policy.effective_dates || 'Pending Review';

        elements.loss_dt.innerText = `${f.loss.date || ''} ${f.loss.time || ''}`.trim() || 'Pending';
        elements.location.innerText = f.loss.location || 'Missing';
        elements.type.innerText = f.claim_type || 'Collision';

        elements.claimant.innerText = f.parties.claimant || 'Missing';
        elements.third.innerText = f.parties.third_parties || 'None Identified';
        elements.contact.innerText = f.parties.contact_details || 'Missing';

        elements.vin.innerText = f.asset.asset_id || 'Missing';
        elements.estimate.innerText = f.asset.estimated_damage ? `$${f.asset.estimated_damage.toLocaleString()}` : 'Missing';
        elements.initial.innerText = f.initial_estimate ? `$${f.initial_estimate.toLocaleString()}` : 'N/A';

        elements.desc.innerText = f.loss.description || 'No description extracted.';
    }

    function getRouteColor(route) {
        switch (route) {
            case 'Fast-track': return '#10b981';
            case 'Manual Review': return '#f59e0b';
            case 'Investigation Flag': return '#ef4444';
            case 'Specialist Queue': return '#3b82f6';
            case 'High-Value Review': return '#a78bfa';
            default: return '#8b5cf6';
        }
    }

    document.querySelector('.export-btn').addEventListener('click', () => {
        if (!window.currentAnalysis) return;
        const blob = new Blob([JSON.stringify(window.currentAnalysis, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `claim_analysis_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    });
});
