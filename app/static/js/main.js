// document.addEventListener('DOMContentLoaded', () => {
//     // Request permission for notifications as soon as the page loads
//     if ('Notification' in window && Notification.permission !== 'granted') {
//         Notification.requestPermission();
//     }

//     // Start checking the time every minute
//     setInterval(checkSchedules, 5000); // 60000 milliseconds = 1 minute
    
//     // Run once on page load as well
//     checkSchedules();
// });

// async function checkSchedules() {
//     try {
//         const response = await fetch('/api/schedules');
//         if (!response.ok) {
//             throw new Error('Could not fetch schedules');
//         }
//         const schedules = await response.json();
//         const now = new Date();
//         const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

//         console.log(`Checking schedules at ${currentTime}`); // For debugging

//         schedules.forEach(schedule => {
//             if (schedule.time === currentTime) {
//                 showNotification(
//                     `Time for your medicine: ${schedule.medicine_name}`,
//                     `Please take your dose of ${schedule.dosage}.`
//                 );
//             }
//         });
//     } catch (error) {
//         console.error('Error fetching schedules:', error);
//     }
// }

// // Add schedule_id as a parameter to the function
// function showNotification(title, body, schedule_id) {
//     if (Notification.permission === 'granted') {
//         const notification = new Notification(title, {
//             body: body,
//             // Add a tag to prevent duplicate notifications if the check runs frequently
//             tag: `med-notification-${schedule_id}` 
//         });

//         // Add the click event handler
//         notification.onclick = () => {
//             fetch('/log-dose', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json',
//                 },
//                 body: JSON.stringify({ schedule_id: schedule_id, status: 'Taken' }),
//             })
//             .then(response => response.json())
//             .then(data => {
//                 console.log('Log status updated:', data.message);
//                 // Optional: Reload the page to show the new history
//                 window.location.reload(); 
//             })
//             .catch((error) => {
//                 console.error('Error:', error);
//             });
//         };
//     }
// }

// // Function to add more time inputs in the form (keep this)
// function addTimeInput() {
//     const container = document.getElementById('time-inputs');
//     const newTimeInput = document.createElement('input');
//     newTimeInput.type = 'time';
//     newTimeInput.name = 'times[]';
//     newTimeInput.required = true;
//     container.appendChild(newTimeInput);
// }

document.addEventListener('DOMContentLoaded', () => {
    // Request permission for notifications as soon as the page loads
    if ('Notification' in window && Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
    // Schedule the first check when the page loads
    scheduleNextNotification();
});

// A variable to hold our timer so we can manage it
let nextNotificationTimer = null;

async function scheduleNextNotification() {
    // Clear any existing timer to avoid duplicates
    if (nextNotificationTimer) {
        clearTimeout(nextNotificationTimer);
    }

    try {
        // 1. Get all schedules from our backend
        const response = await fetch('/api/schedules');
        const schedules = await response.json();
        const now = new Date();

        let nextSchedule = null;
        let minDelay = Infinity;

        // 2. Loop through schedules to find the soonest one in the future
        schedules.forEach(schedule => {
            const [hour, minute] = schedule.time.split(':');
            const scheduleTime = new Date();
            scheduleTime.setHours(hour, minute, 0, 0);

            // If the scheduled time has already passed today, ignore it
            if (scheduleTime < now) {
                return;
            }

            // Calculate how many milliseconds until the scheduled time
            const delay = scheduleTime.getTime() - now.getTime();
            
            // If this is the soonest one we've found so far, save it
            if (delay < minDelay) {
                minDelay = delay;
                nextSchedule = schedule;
            }
        });

        // 3. If we found an upcoming medicine, set a timer for it
        if (nextSchedule) {
            console.log(`Next notification for ${nextSchedule.medicine_name} scheduled in ${Math.round(minDelay / 1000)} seconds.`);
            
            nextNotificationTimer = setTimeout(() => {
                // When timer fires, show the notification
                showNotification(
                    `Time for: ${nextSchedule.medicine_name}`,
                    `Please take your dose of ${nextSchedule.dosage}. Click here to log it as 'Taken'.`,
                    nextSchedule.schedule_id
                );
                // IMPORTANT: Immediately schedule the *next* notification after this one
                scheduleNextNotification();
            }, minDelay);
        } else {
            console.log("No more upcoming medications scheduled for today.");
        }
    } catch (error) {
        console.error('Error scheduling notification:', error);
    }
}


function showNotification(title, body, schedule_id) {
    if (Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: body,
            tag: `med-notification-${schedule_id}`
        });

        notification.onclick = () => {
            fetch('/log-dose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ schedule_id: schedule_id, status: 'Taken' }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Log status updated:', data.message);
                window.location.reload(); // Reload the page to show the new history
            })
            .catch((error) => console.error('Error:', error));
        };
    }
}

// Keep this function for the 'Add Medicine' form
// function addTimeInput() {
//     const container = document.getElementById('time-inputs');
//     const newTimeInput = document.createElement('input');
//     newTimeInput.type = 'time';
//     newTimeInput.name = 'times[]';
//     newTimeInput.className = 'form-control mb-2'; // Bootstrap class
//     newTimeInput.required = true;
//     container.appendChild(newTimeInput);
// }

// In main.js
function addTimeInput() {
    const container = document.getElementById('time-inputs');
    const timeEntryCount = container.getElementsByClassName('time-entry').length;
    const i = timeEntryCount; // Index for the new entry

    const newTimeEntry = document.createElement('div');
    newTimeEntry.className = 'time-entry mb-3';
    
    const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    
    let daySelectorHTML = '<div class="day-selector">';
    for (let j = 0; j < days.length; j++) {
        const day = days[j];
        const dayLabel = dayLabels[j];
        const id = `days_${i}_${day}`;
        const name = `days_${i}_${day}`;
        daySelectorHTML += `
            <input type="checkbox" class="btn-check" id="${id}" name="${name}" autocomplete="off">
            <label class="btn btn-outline-primary btn-sm" for="${id}">${dayLabel}</label>
        `;
    }
    daySelectorHTML += '</div>';

    newTimeEntry.innerHTML = `
        <input type="time" name="times[]" class="form-control mb-2" required>
        ${daySelectorHTML}
    `;
    
    container.appendChild(newTimeEntry);
}