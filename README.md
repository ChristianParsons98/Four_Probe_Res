# Four_Probe_Res

This repository contains Python scripts to automate four-probe resistance measurements using Keithley instruments. It supports both standard and high-precision configurations with the Keithley 2400 SourceMeter and the Keithley 2182 Nanovoltmeter.

## 🧪 Description

The scripts facilitate automated four-probe resistance measurements, commonly used in condensed matter physics and materials science to determine the resistivity of samples. By controlling the Keithley instruments via GPIB, the code enables precise and repeatable measurements, reducing manual intervention and potential errors.

- `K1.py`: Standard precision measurements using only the Keithley 2400 SourceMeter.
- `K2V1.py`: High-precision measurements combining the Keithley 2400 SourceMeter with the Keithley 2182 Nanovoltmeter.

## 🔧 Techniques Used

- **GPIB Communication**: Interfaces with instruments using the General Purpose Interface Bus (GPIB) protocol.
- **Automated Measurement Sequences**: Executes predefined measurement routines to collect resistance data.
- **Data Logging**: Captures and stores measurement data for further analysis.

## 📦 Libraries and Tools

- [PyVISA](https://pyvisa.readthedocs.io/en/latest/): Python library for controlling measurement devices via GPIB.
- [NumPy](https://numpy.org/): Fundamental package for scientific computing with Python.
- [time](https://docs.python.org/3/library/time.html): Provides time-related functions for managing delays and timing.

## 📁 Project Structure

```plaintext
.
├── K1.py
├── K2V1.py
└── README.md
```

### Notable Files

- `K1.py`: Script for standard precision four-probe resistance measurements using the Keithley 2400.
- `K2V1.py`: Script for high-precision measurements using both the Keithley 2400 and 2182.
