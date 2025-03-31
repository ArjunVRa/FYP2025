const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');

allSideMenu.forEach(item=> {
	const li = item.parentElement;

	item.addEventListener('click', function () {
		allSideMenu.forEach(i=> {
			i.parentElement.classList.remove('active');
		})
		li.classList.add('active');
	})
});




// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');

menuBar.addEventListener('click', function () {
	sidebar.classList.toggle('hide');
})





const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
	if(window.innerWidth < 576) {
		e.preventDefault();
		searchForm.classList.toggle('show');
		if(searchForm.classList.contains('show')) {
			searchButtonIcon.classList.replace('bx-search', 'bx-x');
		} else {
			searchButtonIcon.classList.replace('bx-x', 'bx-search');
		}
	}
})





if(window.innerWidth < 768) {
	sidebar.classList.add('hide');
} else if(window.innerWidth > 576) {
	searchButtonIcon.classList.replace('bx-x', 'bx-search');
	searchForm.classList.remove('show');
}


window.addEventListener('resize', function () {
	if(this.innerWidth > 576) {
		searchButtonIcon.classList.replace('bx-x', 'bx-search');
		searchForm.classList.remove('show');
	}
})



const switchMode = document.getElementById('switch-mode');

switchMode.addEventListener('change', function () {
	if(this.checked) {
		document.body.classList.add('dark');
	} else {
		document.body.classList.add('dark');
	}
})

document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("upload-form");
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    const resultContainer = document.getElementById("result-container");
    const positiveSpan = document.getElementById("positive");
    const negativeSpan = document.getElementById("negative");
    const neutralSpan = document.getElementById("neutral");

    uploadForm.addEventListener("submit", function (e) {
        e.preventDefault();

        // Hide the upload form and show the progress bar
        uploadForm.style.display = "none";
        progressContainer.style.display = "block";

        // Create a FormData object to send the file
        const formData = new FormData(uploadForm);

        // Create an XMLHttpRequest to send the file for processing
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload_and_analyze", true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressBar.value = percent;
                progressText.textContent = `Processing... ${percent.toFixed(2)}%`;
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                positiveSpan.textContent = data.positive.toFixed(2);
                negativeSpan.textContent = data.negative.toFixed(2);
                neutralSpan.textContent = data.neutral.toFixed(2);

                // Hide the progress bar and show the result
                progressContainer.style.display = "none";
                resultContainer.style.display = "block";
            }
        };

        xhr.send(formData);
    });
});



 // Display the preloader initially
document.querySelector('.preloader');

// Hide the preloader after 2 seconds
setTimeout(function() {
document.querySelector('.preloader').style.display = 'none';
}, 4000); // 2000 milliseconds (2 seconds)
