package main

import (
    "html/template"
    "net/http"
)

type Config struct {

    Baseurl     string
    Pagetitle   string
    RootDir     string

}


func handler(w http.ResponseWriter, r *http.Request) {

    t, _ := template.ParseFiles("web/templates/index.html")
    name := "World"
    t.Execute(w, name)

}


func main() {

    http.HandleFunc("/", handler)
    http.ListenAndServe(":8080", nil)

}
