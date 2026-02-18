importScripts("https://www.gstatic.com/firebasejs/12.6.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.6.0/firebase-messaging-compat.js");

firebase.initializeApp({
    apiKey: "AIzaSyCEVCeD8QbdOFG1MMk0LKi6FNAoGY3cL9E",
    authDomain: "push-notification-cc870.firebaseapp.com",
    projectId: "push-notification-cc870",
    messagingSenderId: "push-notification-cc870",
    appId: "1:595457578638:web:42a5525e4f017186e4dbdf",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
    console.log("Background message received:", payload);

    self.registration.showNotification(
        payload.notification.title,
        {
            body: payload.notification.body,
            icon: "/static/images/logo.png"
        }
    );
});





// importScripts("https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js");
// importScripts("https://www.gstatic.com/firebasejs/12.6.0/firebase-messaging.js");

// firebase.initializeApp({
//     apiKey: "AIzaSyCEVCeD8QbdOFG1MMk0LKi6FNAoGY3cL9E",
//     authDomain: "push-notification-cc870.firebaseapp.com",
//     projectId: "push-notification-cc870",
//     messagingSenderId: "595457578638",
// });

// const messaging = firebase.messaging();

// messaging.onBackgroundMessage(function(payload) {
//     const title = payload.notification.title;
//     const options = { body: payload.notification.body };
//     self.registration.showNotification(title, options);
// });
