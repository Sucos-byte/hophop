# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Frozen analytical regression workflow; separate selection and locked scoring."""

from pathlib import Path
import sys

from analytical_reference import _json_bytes,_sha256
from analytical_design import load_design_record
from atomic_outputs import publish_outputs
from green_ops_build_dataset import ArgumentParser
from ml_dataset import materialize_dataset,load_dataset,publish_files
from ml_pipeline import model_from_bytes,predict_record
from ml_workflow import train_selection,locked_evaluation


def main(argv=None):
    parser=ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    materialize=commands.add_parser('materialize');materialize.add_argument('--recipe',type=Path,required=True)
    materialize.add_argument('--output-dir',type=Path,required=True)
    for name in ('train','evaluate'):
        sub=commands.add_parser(name);sub.add_argument('--dataset',type=Path,required=True);sub.add_argument('--output-dir',type=Path,required=True)
        if name=='evaluate':sub.add_argument('--training',type=Path,required=True)
    sub=commands.add_parser('predict');sub.add_argument('--model',type=Path,required=True)
    sub.add_argument('--artifact-dir',type=Path,required=True);sub.add_argument('--output',type=Path,required=True)
    sub.add_argument('--recipe',type=Path,required=True)
    sub.add_argument('--domain',choices=('primary','declared_stress'),default='primary')
    args=parser.parse_args(argv)
    try:
        if args.command=='predict':
            output=args.output.expanduser().resolve();source=args.artifact_dir.resolve()
            if output in (args.model.resolve(),args.recipe.resolve()) or source==output or source in output.parents:raise ValueError('prediction output aliases input sources')
            model_bytes=args.model.read_bytes();model=model_from_bytes(model_bytes);record=load_design_record(source)
            recipe_bytes=args.recipe.read_bytes();value=predict_record(model,record,domain=args.domain,recipe_bytes=recipe_bytes)
            prediction=dict(prediction_version=1,provenance='analytical_simulation',target=model['target'],unit=model['unit'],
                run_id=record['row']['run_id'],value=value,domain=args.domain,model_sha256=_sha256(model_bytes),
                input_manifest_sha256=record['manifest_sha256'],recipe_sha256=_sha256(recipe_bytes),feature_order=model['feature_order'])
            publish_outputs({output:_json_bytes(prediction).decode('utf-8')})
        else:
            output=args.output_dir.expanduser().resolve()
            if output.exists():raise ValueError('output directory must be new')
            inputs=[args.recipe.resolve()] if args.command=='materialize' else [args.dataset.resolve()]
            if args.command=='evaluate':inputs.append(args.training.resolve())
            if any(output==source or source in output.parents for source in inputs):raise ValueError('output aliases input sources')
            if args.command=='materialize':materialize_dataset(args.recipe,output,progress=print)
            else:
                dataset=load_dataset(args.dataset,progress=print)
                files=train_selection(dataset) if args.command=='train' else locked_evaluation(dataset,args.training)
                publish_files(output,files)
    except (OSError,UnicodeError,ValueError) as error:
        print(f'error: {error}',file=sys.stderr);return 1
    print(f'{args.command}: completed analytical_simulation workflow.')
    return 0


if __name__=='__main__':raise SystemExit(main())
