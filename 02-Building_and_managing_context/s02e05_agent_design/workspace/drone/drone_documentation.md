---
meta-viewport: width=device-width, initial-scale=1
title: DRN-BMB7 - instrukcja API
---


DRN\-BMB7 \- instrukcja obsługi API
====================================

Dokumentacja dotyczy fikcyjnego drona bojowego **DRN\-BMB7** używanego w grze.

Oprogramowanie: **Softo Inc.**, rok 2026\.

API pozwala sterować wieloma elementami drona. Nazwy metod mogą się powtarzać (na przykład kilka wariantów `set(...)`). System rozpoznaje właściwe polecenie na podstawie przekazanych parametrów.

**Informacja operacyjna:** model DRN\-BMB7 zawsze niesie jeden ładunek wybuchowy małego zasięgu.

Endpoint i wymagania requestu
-----------------------------

POST`/verify`

* `apikey` \- UUID identyfikujące operatora drona (pole obowiązkowe)
* `task` \- nazwa zadania, zawsze ustawiona na `drone` (pole obowiązkowe)
* `answer` \- obiekt z danymi odpowiedzi przekazywanymi do zadania (pole obowiązkowe)
* `answer.instructions` \- tablica JSON z instrukcjami (co najmniej 1 element)


Metody sterowania
-----------------

| Obszar | Metoda | Opis i parametry | Przykład |
| --- | --- | --- | --- |
| Sterowanie lokalizacją | `setDestinationObject(ID)` | Ustawia obiekt docelowy lotu.     Format `ID`: `[A-Z]{3}[0-9]+[A-Z]{2}`     Struktura: prefix typu obiektu \+ kod liczbowy \+ kod kraju. | `setDestinationObject(BLD1234PL)` |
| Sterowanie lokalizacją | `set(x,y)` | Ustawia sektor lądowania na mapie obiektu.   `x` to kolumna, `y` to wiersz.     Lewy górny róg mapy ma współrzędne `1,1`. | `set(3,4)` |
| Sterowanie silnikami | `set(mode)` | Włącza lub wyłącza silniki. Dozwolone wartości: `engineON`, `engineOFF`. | `set(engineON)` |
| Sterowanie silnikami | `set(power)` | Ustawia moc silników od `0%` do `100%`. | `set(1%)` |
| Sterowanie dronem | `set(xm)` | Ustawia wysokość lotu od `1m` do `100m`. | `set(4m)` |
| Sterowanie dronem | `flyToLocation` | Rozpoczyna lot i nie przyjmuje parametrów.     Wymaga wcześniejszego ustawienia wysokości, obiektu docelowego i sektora lądowania. | `flyToLocation` |
| Diagnostyka | `selfCheck` | Wykonuje szybki test systemów pokładowych i zwraca, czy wszystkie moduły są gotowe. | `selfCheck` |
| Konfiguracja | `setName(x)` | Ustawia przyjazną nazwę drona. Wartość `x` musi być alfanumeryczna i może zawierać spacje. | `setName(Fox 21)` |
| Konfiguracja | `setOwner(Imie Nazwisko)` | Ustawia właściciela drona.     Trzeba podać dokładnie dwa słowa oddzielone spacją: imię i nazwisko. | `setOwner(Adam Kowalski)` |
| Konfiguracja | `setLed(color)` | Ustawia kolor LED. Parametr `color` to kod HEX w formacie `#000000`. | `setLed(#00FFAA)` |
| Informacyjne | `getFirmwareVersion` | Zwraca wersję oprogramowania zainstalowaną w dronie. Metoda bez parametrów. | `getFirmwareVersion` |
| Informacyjne | `getConfig` | Zwraca aktualną konfigurację drona. Metoda bez parametrów.     Odpowiedź zawiera także pole `owner` (domyślnie: `not assigned`). | `getConfig` |
| Kalibracja | `calibrateCompass` | Kalibruje system orientacji przestrzennej oparty o kompas. Metoda bez parametrów. | `calibrateCompass` |
| Kalibracja | `calibrateGPS` | Kalibruje nadajnik i odbiornik GPS. Metoda bez parametrów. | `calibrateGPS` |
| Serwis | `hardReset` | Przywraca konfigurację drona do stanu fabrycznego. Metoda bez parametrów. | `hardReset` |


Ustawienia celu misji
---------------------

Można ustawić wiele celów, jeden po drugim:

* `set(video)` \- nagranie filmu
* `set(image)` \- wykonanie zdjęcia
* `set(destroy)` \- zniszczenie obiektu
* `set(return)` \- powrót do bazy z raportem po misji


Kolejność celów nie jest istotna. System AI zaszyty w dronie wykona wszystkie cele w odpowiedniej kolejności.

Przykłady użycia funkcji
--------------------------

### 1\) Szybki test systemów, konfiguracja i odczyt wersji

    {
      "apikey": "tutaj-twoj-klucz",
      "task": "drone",
      "answer": {
        "instructions": [
          "selfCheck",
          "getConfig",
          "getFirmwareVersion"
        ]
      }
    }

### 2\) Personalizacja drona (nazwa \+ właściciel \+ LED)

    {
      "apikey": "tutaj-twoj-klucz",
      "task": "drone",
      "answer": {
        "instructions": [
          "setName(Fox 21)",
          "setOwner(Adam Kowalski)",
          "setLed(#FF8800)"
        ]
      }
    }

### 3\) Kalibracja systemów nawigacji

    {
      "apikey": "tutaj-twoj-klucz",
      "task": "drone",
      "answer": {
        "instructions": [
          "calibrateCompass",
          "calibrateGPS",
          "selfCheck"
        ]
      }
    }

### 4\) Przywrócenie ustawień fabrycznych

    {
      "apikey": "tutaj-twoj-klucz",
      "task": "drone",
      "answer": {
        "instructions": [
          "hardReset",
          "getConfig"
        ]
      }
    }

Odpowiedź API
--------------

W odpowiedzi API zwraca dane zgodne z celem misji, na przykład:

* materiał wideo,
* zdjęcia,
* status wykonania misji,
* raport powrotu do bazy.
