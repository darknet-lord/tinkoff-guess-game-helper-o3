use pyo3::prelude::*;
use tinkoff_guess_game_lib::{suggest_words, strings_to_words, guess_word};

#[pyfunction]
fn suggest() -> Vec<&'static str> {
    let suggestions = suggest_words();
    suggestions
}

#[pyfunction]
fn guess(strings: Vec<String>) -> Vec<&'static str> {
    let previous_words = strings_to_words(strings);
    return guess_word(previous_words);
}

#[pymodule]
#[pyo3(name = "tinkoff_guess_game_helper_py")]
fn o3(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(suggest, m)?)?;
    m.add_function(wrap_pyfunction!(guess, m)?)?;
    Ok(())
}
