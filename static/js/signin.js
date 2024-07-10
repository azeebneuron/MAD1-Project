document.addEventListener('DOMContentLoaded', function () {
    const signInBtn = document.getElementById('signInBtn');
    const signUpBtn = document.getElementById('signUpBtn');
    const signInForm = document.getElementById('signInForm');
    const signUpForm = document.getElementById('signUpForm');

    signInBtn.addEventListener('click', function () {
        signInForm.classList.remove('hidden');
        signUpForm.classList.add('hidden');
    });

    signUpBtn.addEventListener('click', function () {
        signUpForm.classList.remove('hidden');
        signInForm.classList.add('hidden');
    });
});
