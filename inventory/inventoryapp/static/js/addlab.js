function addlabjs ()
{
    const labPatterns = {
        et: [
            /^Electrician(\d*)$/,
            /^Electric(\d*)$/,
            /^ET(\d*)$/,
            /^ET_Lab(\d*)$/,
            /^ET_Lab_(\d*)$/,
             /^ET lab(\d*)$/,
            /^ET_lab_(\d*)$/,
            /^ET_lab$/
        ],
        stitch: [
            /^Stitchingand Tailoring(\d*)$/, /^Stitching&Tailoring(\d*)$/, /^Stitching & Tailoring(\d*)$/, /^Stitching_and_Tailoring(\d*)$/,
            /^Stitching_&_Tailoring(\d*)$/, /^S&T(\d*)$/, /^S_&_T(\d*)$/, /^Stitching(\d*)$/, /^Tailoring(\d*)$/
        ],
        beauty: [/^Beauty and Wellness(\d*)$/, /^ Beauty&Wellness(\d*)$/, /^Beauty & Wellness(\d*)$/, /^Beauty_and_Wellness(\d*)$/, /^B&W(\d*)$/,
            /^Beauty_&_Wellness(\d*)$/, /^B & W(\d*)$/, /^Beauty(\d*)$/],
    };
    const sectionChoices =
    {
        et: [
            { value: 'Electrical Technician', text: 'Electrical Technician' },
            { value: 'CCTV', text: 'CCTV' },
            { value: 'Solar', text: 'Solar' },
            { value: 'Motor Starter', text: 'Motor Starter' },
            { value: 'Cabling Technician', text: 'Cabling Technician' },
            { value: 'EV Charging', text: 'EV Charging' },
            { value: 'Energy Meter', text: 'Energy Meter' },
            { value: "Create New Section", text: "Create New Section" }
        ],
        beauty: [{ value: 'Skin', text: 'Skin' }, { value: 'Hair', text: 'Hair' }, { value: 'Nails', text: 'Nails' }, { value: 'Makeup', text: 'Makeup' },
        { value: "Create New Section", text: "Create New Section" }],
        stitch: [{ value: 'Basic', text: 'Basic' }, { value: 'Advanced', text: 'Advanced' }, { value: 'Knitting', text: 'Knitting' },
        { value: "Create New Section", text: "Create New Section" }]
    };
    document.addEventListener('DOMContentLoaded', () => {
        const nameInput = document.getElementById('id_Name');
        const sectionSelect = document.getElementById('id_Section');
        const originalOptions = Array.from(sectionSelect.options).map(opt => ({ value: opt.value, text: opt.text }));
        console.log(sectionSelect);

        function setOptions(selectEl, opts) {
            selectEl.innerHTML = '';
            opts.forEach(({ value, text }) => {
                const option = document.createElement("option");
                option.value = value;
                option.text = text;
                selectEl.appendChild(option);
            });
        }

        // Delegate Section changes for dynamically added selects
        document.getElementById("equipment-container").addEventListener("change", e => {
            if (!e.target.name.startsWith("Section")) return;

            const sectionSelect = e.target;
            const indexMatch = sectionSelect.name.match(/(\d+)$/);
            const index = indexMatch ? indexMatch[1] : null;

            const nameInput = document.getElementById("id_Name");
            if (!nameInput) return;
            const nameVal = nameInput.value.trim();

            let matchedCategory = null;
            if (labPatterns.et.some(rx => rx.test(nameVal))) matchedCategory = 'et';
            else if (labPatterns.stitch.some(rx => rx.test(nameVal))) matchedCategory = 'stitch';
            else if (labPatterns.beauty.some(rx => rx.test(nameVal))) matchedCategory = 'beauty';

            if (sectionSelect.value === "Create New Section") {
                // Create new label + input field for user-defined section
                const existingInput = document.getElementById("newsection" + index);
                if (existingInput) return; // Prevent duplicates

                const label = document.createElement("label");
                label.textContent = "New Section:";
                label.setAttribute("for", "newsection" + index);

                const input = document.createElement("input");
                input.id = "newsection" + index;
                input.name = "newsection" + index;
                input.type = "text";
                input.value = "";

                sectionSelect.insertAdjacentElement("afterend", label);
                label.insertAdjacentElement("afterend", input);
            } else if (matchedCategory) {
                setOptions(sectionSelect, sectionChoices[matchedCategory]);
            }
        });

        // Watch the lab name input and reapply options
       // const nameInput = document.getElementById("id_Name");
        if (nameInput) {
            nameInput.addEventListener("input", () => {
                const nameVal = nameInput.value.trim();

                let matchedCategory = null;
                if (labPatterns.et.some(rx => rx.test(nameVal))) matchedCategory = 'et';
                else if (labPatterns.stitch.some(rx => rx.test(nameVal))) matchedCategory = 'stitch';
                else if (labPatterns.beauty.some(rx => rx.test(nameVal))) matchedCategory = 'beauty';

                document.querySelectorAll("#equipment-container select[name^='Section']").forEach(select => {
                    if (matchedCategory) {
                        setOptions(select, sectionChoices[matchedCategory]);
                    }
                });
            });
        }
    })
}
addlabjs();