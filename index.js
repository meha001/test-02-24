const user = {
    name: "Vasya",
    company: [
        {name: "Hexlet", platform:{name: "moodle"}},
        {name: "web doctor"},
    ]
}

const func = (obj) => {
    return Object.assign(obj, {company: [
        {name: "Hexlet", platform:{name: "moodle", clients:500}},
        {name: "web doctor"},
    ]})
}

console.log(JSON.stringify(func(user)))