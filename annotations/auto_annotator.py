import time
from typing import List

import gspread


class Sample:
    __slots__ = ['sample_accession', 'stress_type', 'stress_intensity', 'stress_duration', 'is_control', 'tissue',
                 'age', 'genotype', 'experiment_group', 'differentiating_factors']

    def __init__(self, sample_accession: str,
                 stress_type: str,
                 stress_intensity: str,
                 stress_duration: str,
                 is_control: bool,
                 tissue: str,
                 age: str,
                 genotype: str):
        self.sample_accession: str = sample_accession
        self.stress_type: str = stress_type
        self.stress_intensity: str = stress_intensity
        self.stress_duration: str = stress_duration
        self.is_control: bool = is_control
        self.tissue: str = tissue
        self.age: str = age
        self.genotype: str = genotype
        self.experiment_group: str = ""
        self.differentiating_factors:List[str] = []

    def __repr__(self):
        return f"Sample {self.sample_accession} under {self.stress_type} stress {self.stress_intensity} intensity for {self.stress_duration} hours. Sample taken from {self.tissue} of {self.age} plant of {self.genotype}. Sample is in {self.experiment_group}"


class Study:
    __slots__ = ['study_accession', 'samples']

    def __init__(self, study_accession):
        self.study_accession: str = study_accession
        self.samples: List[Sample] = []

    def __repr__(self):
        return f"Study {self.study_accession} with {len(self.samples)} samples and {self.differentiating_factors} as differentiating factors"

    def find_differentiating_factors(self):
        """Find the differentiating factors for the study"""
        stress_intensities = set()
        tissues = set()
        ages = set()
        genotypes = set()
        for sample in self.samples:
            stress_intensities.add(sample.stress_intensity)
            tissues.add(sample.tissue)
            ages.add(sample.age)
            genotypes.add(sample.genotype)
        for sample in self.samples:
            if len(stress_intensities) != 1:
                sample.differentiating_factors.append(sample.stress_intensity)
            if len(tissues) != 1:
                sample.differentiating_factors.append(sample.tissue)
            if len(ages) != 1:
                sample.differentiating_factors.append(sample.age)
            if len(genotypes) != 1:
                sample.differentiating_factors.append(sample.genotype)
            sample.differentiating_factors = sample.differentiating_factors[:3]

    def find_experiment_group(self):
        """Find the experiment group of the sample"""
        experiment_groups = {}
        for sample in self.samples:
            if (temp := tuple(sample.differentiating_factors)) not in experiment_groups:
                experiment_groups[temp] = "Group " + chr(len(experiment_groups) + 65)
            sample.experiment_group = experiment_groups[temp]


def connect_to_google_sheet() -> gspread.Worksheet:
    """Connect to Google Sheets and return the worksheet"""
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open('Annotation_2_MG')
    return sh.get_worksheet(1)


def load_data(values):
    studies: List[Study] = []
    study_accessions: List[str] = []
    for sample_list in values:
        study_accession: str = sample_list[6]
        # Check if the study already exists
        if study_accession not in study_accessions:
            # Create a Study object and add it to the list of studies
            study = Study(study_accession)
            studies.append(study)
            study_accessions.append(study_accession)
        else:
            study = studies[study_accessions.index(study_accession)]

        # Create a Sample object and add it to the study
        sample_accession = sample_list[24]
        stress_type = sample_list[17]
        stress_intensity = sample_list[19]
        stress_duration = sample_list[20]
        is_control = sample_list[21] == 'Control'
        tissue = sample_list[29]
        age = sample_list[30]
        genotype = sample_list[31]
        sample = Sample(sample_accession, stress_type, stress_intensity, stress_duration, is_control, tissue, age,
                        genotype)
        study.samples.append(sample)
    return studies


def save_data(studies, worksheet):
    for study in studies:
        for sample in study.samples:
            print("Now going to sleep, to wait for API call limit to reset.")
            time.sleep(10)
            worksheet.update_acell(f'AQ{worksheet.find(sample.sample_accession).row}', sample.experiment_group)
            try:
                worksheet.update_acell(f'AR{worksheet.find(sample.sample_accession).row}', sample.differentiating_factors[0])
                worksheet.update_acell(f'AS{worksheet.find(sample.sample_accession).row}', sample.differentiating_factors[1])
                worksheet.update_acell(f'AT{worksheet.find(sample.sample_accession).row}', sample.differentiating_factors[2])
            except IndexError:
                pass
def main():
    worksheet: gspread.Worksheet = connect_to_google_sheet()
    # Get all values from the worksheet
    values: List[str] = worksheet.get_all_values()[1:]
    print(values[-1])
    # Create a list of Study objects
    studies = load_data(values)

    for study in studies:
        study.find_differentiating_factors()
        study.find_experiment_group()
    print("Data ready to be saved. Now going to sleep, to wait for API call limit to reset.")
    time.sleep(60)

    save_data(studies, worksheet)


if __name__ == '__main__':
    main()
